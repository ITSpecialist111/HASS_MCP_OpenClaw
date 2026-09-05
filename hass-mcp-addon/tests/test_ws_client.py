"""Regression tests for the persistent Home Assistant WebSocket client."""

import asyncio
import json
from contextlib import suppress
from unittest.mock import AsyncMock, patch

import pytest
from websockets.protocol import State

from app.ws_client import HAWebSocket


class FakeConnection:
    def __init__(self, auth_response=None, state=State.OPEN):
        self.state = state
        self.sent = []
        self._auth_responses = [
            {"type": "auth_required"},
            auth_response or {"type": "auth_ok"},
        ]
        self._incoming = asyncio.Queue()
        self.close = AsyncMock(side_effect=self._close)

    async def recv(self):
        if self._auth_responses:
            return json.dumps(self._auth_responses.pop(0))
        return await self._incoming.get()

    async def send(self, raw):
        message = json.loads(raw)
        self.sent.append(message)
        if "id" in message:
            await self._incoming.put(
                json.dumps({"id": message["id"], "success": True, "result": "ok"})
            )

    def __aiter__(self):
        return self

    async def __anext__(self):
        message = await self._incoming.get()
        if message is None:
            raise StopAsyncIteration
        return message

    async def finish(self):
        await self._incoming.put(None)

    async def _close(self):
        self.state = State.CLOSED
        await self.finish()


class BlockingAuthConnection(FakeConnection):
    def __init__(self):
        super().__init__()
        self.auth_sent = asyncio.Event()
        self._recv_count = 0

    async def recv(self):
        self._recv_count += 1
        if self._recv_count == 1:
            return json.dumps({"type": "auth_required"})
        await asyncio.Event().wait()

    async def send(self, raw):
        self.sent.append(json.loads(raw))
        self.auth_sent.set()


class LegacyOpenConnection:
    closed = False


async def stop_reader(client, connections):
    """Stop test readers without asking the client to reconnect."""
    task = client._reader_task
    client._ws = object()
    for connection in connections:
        await connection.finish()
    if task is not None:
        with suppress(asyncio.CancelledError):
            await asyncio.wait_for(task, timeout=1)


@pytest.mark.asyncio
async def test_sequential_connect_calls_open_once():
    client = HAWebSocket(token="token")
    connections = []

    def make_connection(*_args, **_kwargs):
        connection = FakeConnection()
        connections.append(connection)
        return connection

    with patch(
        "app.ws_client.websockets.connect", new=AsyncMock(side_effect=make_connection)
    ) as connect:
        await client.connect()
        await asyncio.sleep(0)
        await client.connect()

    try:
        assert connect.await_count == 1
    finally:
        await stop_reader(client, connections)


@pytest.mark.asyncio
async def test_concurrent_connect_calls_open_once():
    client = HAWebSocket(token="token")
    connections = []

    def make_connection(*_args, **_kwargs):
        connection = FakeConnection()
        connections.append(connection)
        return connection

    with patch(
        "app.ws_client.websockets.connect", new=AsyncMock(side_effect=make_connection)
    ) as connect:
        await asyncio.gather(*(client.connect() for _ in range(5)))

    try:
        assert connect.await_count == 1
    finally:
        await stop_reader(client, connections)


@pytest.mark.asyncio
async def test_send_calls_reuse_one_connection():
    client = HAWebSocket(token="token")
    connection = FakeConnection()

    with patch(
        "app.ws_client.websockets.connect", new=AsyncMock(return_value=connection)
    ) as connect:
        assert await client.send({"type": "first"}) == {
            "id": 1,
            "success": True,
            "result": "ok",
        }
        assert await client.send({"type": "second"}) == {
            "id": 2,
            "success": True,
            "result": "ok",
        }

    try:
        assert connect.await_count == 1
    finally:
        await stop_reader(client, [connection])


@pytest.mark.asyncio
async def test_stale_reader_cannot_clear_new_connection():
    client = HAWebSocket(token="token")
    old_connection = FakeConnection()
    new_connection = FakeConnection()
    pending = asyncio.get_running_loop().create_future()
    client._ws = new_connection
    client._connected.set()
    client._pending[7] = pending

    with patch.object(client, "_reconnect_loop", new=AsyncMock()) as reconnect:
        reader = asyncio.create_task(client._reader(old_connection))
        await old_connection.finish()
        await reader

    assert client._ws is new_connection
    assert client._connected.is_set()
    assert client._pending[7] is pending
    assert not pending.done()
    reconnect.assert_not_awaited()


@pytest.mark.asyncio
async def test_current_reader_starts_one_replacement():
    client = HAWebSocket(token="token")
    connection = FakeConnection()
    client._ws = connection
    client._connected.set()
    real_sleep = asyncio.sleep

    with (
        patch.object(client, "connect", new=AsyncMock()) as connect,
        patch("app.ws_client.asyncio.sleep", new=AsyncMock()),
    ):
        reader = asyncio.create_task(client._reader(connection))
        await connection.finish()
        await reader
        await real_sleep(0)
        await real_sleep(0)

    assert client._ws is None
    assert not client._connected.is_set()
    connect.assert_awaited_once()


@pytest.mark.asyncio
async def test_authentication_failure_closes_candidate():
    client = HAWebSocket(token="token")
    connection = FakeConnection(auth_response={"type": "auth_invalid"})

    with (
        patch("app.ws_client.websockets.connect", new=AsyncMock(return_value=connection)),
        patch(
            "app.ws_client.asyncio.sleep",
            new=AsyncMock(side_effect=asyncio.CancelledError),
        ),
        pytest.raises(asyncio.CancelledError),
    ):
        await client.connect()

    connection.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_cancellation_during_authentication_closes_candidate():
    client = HAWebSocket(token="token")
    connection = BlockingAuthConnection()

    with patch("app.ws_client.websockets.connect", new=AsyncMock(return_value=connection)):
        task = asyncio.create_task(client.connect())
        await connection.auth_sent.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    connection.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_legacy_closed_flag_reuses_open_connection():
    client = HAWebSocket(token="token")
    client._ws = LegacyOpenConnection()

    with patch("app.ws_client.websockets.connect", new=AsyncMock()) as connect:
        await client.connect()

    connect.assert_not_awaited()


@pytest.mark.asyncio
async def test_closed_state_opens_replacement():
    client = HAWebSocket(token="token")
    client._ws = FakeConnection(state=State.CLOSED)
    replacement = FakeConnection()

    with patch(
        "app.ws_client.websockets.connect", new=AsyncMock(return_value=replacement)
    ) as connect:
        await client.connect()

    try:
        connect.assert_awaited_once()
        assert client._ws is replacement
    finally:
        await stop_reader(client, [replacement])
