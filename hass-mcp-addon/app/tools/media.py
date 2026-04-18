"""§19 Cameras / media."""
from __future__ import annotations

import base64

from .. import hass
from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def camera_snapshot(entity_id: str) -> dict:
        """§19 Snapshot from a camera entity (returns base64 JPEG)."""
        img = await hass.get_camera_image(entity_id)
        return {"entity_id": entity_id, "mime": "image/jpeg",
                "size": len(img),
                "base64": base64.b64encode(img).decode()}

    @tool(mcp)
    async def camera_record(entity_id: str, duration: int = 30,
                              filename: str = "/media/recording.mp4") -> dict:
        """§19 camera.record service."""
        return await ws().call("call_service", domain="camera", service="record",
                                service_data={"entity_id": entity_id,
                                              "duration": duration,
                                              "filename": filename})

    @tool(mcp)
    async def camera_play_stream(entity_id: str, media_player: str) -> dict:
        """§19 Cast a camera stream to a media player."""
        return await ws().call("call_service", domain="camera", service="play_stream",
                                service_data={"entity_id": entity_id,
                                              "media_player": media_player})

    @tool(mcp)
    async def media_player_browse(entity_id: str, media_content_id: str | None = None,
                                    media_content_type: str | None = None) -> dict:
        """§19 Browse media tree."""
        kwargs: dict = {"entity_id": entity_id}
        if media_content_id is not None: kwargs["media_content_id"] = media_content_id
        if media_content_type is not None: kwargs["media_content_type"] = media_content_type
        return await ws().call("media_player/browse_media", **kwargs)

    @tool(mcp)
    async def media_player_search(entity_id: str, query: str,
                                    media_filter_classes: list[str] | None = None) -> dict:
        """§19 Search media."""
        kwargs = {"entity_id": entity_id, "search_query": query}
        if media_filter_classes: kwargs["media_filter_classes"] = media_filter_classes
        return await ws().call("media_player/search_media", **kwargs)

    @tool(mcp)
    async def media_player_play_media(entity_id: str, media_content_id: str,
                                        media_content_type: str = "music",
                                        announce: bool = False,
                                        extra: dict | None = None) -> dict:
        """§19 Play media."""
        data = {"entity_id": entity_id,
                "media_content_id": media_content_id,
                "media_content_type": media_content_type,
                "announce": announce}
        if extra: data["extra"] = extra
        return await ws().call("call_service", domain="media_player",
                                service="play_media", service_data=data)

    @tool(mcp)
    async def tts_speak(entity_id: str, message: str,
                          language: str | None = None,
                          options: dict | None = None,
                          cache: bool = True) -> dict:
        """§19 TTS speak via tts.speak."""
        data = {"entity_id": entity_id, "message": message, "cache": cache}
        if language: data["language"] = language
        if options: data["options"] = options
        return await ws().call("call_service", domain="tts", service="speak",
                                service_data=data)

    @tool(mcp)
    async def stt_transcribe(audio_b64: str, mime: str = "audio/wav",
                              language: str = "en-US",
                              engine: str | None = None) -> dict:
        """§19 STT transcription via stt.* service (requires engine)."""
        data = {"audio": audio_b64, "format": mime, "language": language}
        target_engine = engine or "stt.home_assistant_cloud"
        return await ws().call("call_service",
                                domain=target_engine.split(".")[0],
                                service="transcribe",
                                service_data=data,
                                target={"entity_id": target_engine})

    @tool(mcp)
    async def wake_word_test(audio_b64: str, engine: str | None = None) -> dict:
        """§19 Wake word test by sending audio to wake_word/* (best-effort)."""
        return await ws().call("wake_word/run",
                                **({"engine_id": engine} if engine else {}))

    return 9
