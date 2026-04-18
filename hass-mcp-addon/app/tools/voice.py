"""§32 Voice assistants / pipelines."""
from __future__ import annotations

from typing import Any

from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def list_pipelines() -> Any:
        """§32 List Assist pipelines."""
        return await ws().call("assist_pipeline/pipeline/list")

    @tool(mcp)
    async def create_pipeline(name: str, language: str,
                                conversation_engine: str, tts_engine: str,
                                stt_engine: str, **fields) -> Any:
        """§32 Create an Assist pipeline."""
        return await ws().call("assist_pipeline/pipeline/create",
                                name=name, language=language,
                                conversation_engine=conversation_engine,
                                tts_engine=tts_engine, stt_engine=stt_engine,
                                **fields)

    @tool(mcp)
    async def update_pipeline(pipeline_id: str, patch: dict) -> Any:
        """§32 Update an Assist pipeline."""
        return await ws().call("assist_pipeline/pipeline/update",
                                pipeline_id=pipeline_id, **patch)

    @tool(mcp)
    async def delete_pipeline(pipeline_id: str) -> Any:
        """§32 Delete a pipeline."""
        return await ws().call("assist_pipeline/pipeline/delete",
                                pipeline_id=pipeline_id)

    @tool(mcp)
    async def set_preferred_pipeline(pipeline_id: str) -> Any:
        """§32 Set preferred pipeline."""
        return await ws().call("assist_pipeline/pipeline/set_preferred",
                                pipeline_id=pipeline_id)

    @tool(mcp)
    async def run_pipeline(start_stage: str = "intent", end_stage: str = "tts",
                            input_data: dict | None = None,
                            pipeline_id: str | None = None) -> Any:
        """§32 Run an Assist pipeline (text-only by default)."""
        kwargs: dict[str, Any] = {"start_stage": start_stage, "end_stage": end_stage,
                                   "input": input_data or {}}
        if pipeline_id: kwargs["pipeline"] = pipeline_id
        return await ws().call("assist_pipeline/run", **kwargs)

    @tool(mcp)
    async def list_wake_words() -> Any:
        """§32 List wake word providers."""
        return await ws().call("wake_word/info")

    @tool(mcp)
    async def list_stt_engines() -> Any:
        """§32 List STT engines."""
        return await ws().call("stt/engine/list")

    @tool(mcp)
    async def list_tts_engines() -> Any:
        """§32 List TTS engines."""
        return await ws().call("tts/engine/list")

    @tool(mcp)
    async def list_conversation_agents() -> Any:
        """§32 List conversation agents."""
        return await ws().call("conversation/agent/list")

    @tool(mcp)
    async def intent_handle(intent_type: str, slots: dict | None = None) -> Any:
        """§32 Handle an intent."""
        return await ws().call("intent/handle", intent={"name": intent_type,
                                                         "data": slots or {}})

    return 11
