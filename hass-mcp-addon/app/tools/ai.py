"""§33 AI / LLM integrations (delegates to whichever integrations are present)."""
from __future__ import annotations

from typing import Any

from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def openai_conversation_send(agent_id: str, text: str,
                                         conversation_id: str | None = None,
                                         language: str = "en") -> Any:
        """§33 Send text to a conversation agent (typically OpenAI/Anthropic/etc.)."""
        kwargs: dict[str, Any] = {"text": text, "language": language,
                                    "agent_id": agent_id}
        if conversation_id: kwargs["conversation_id"] = conversation_id
        return await ws().call("conversation/process", **kwargs)

    @tool(mcp)
    async def openai_image_generate(prompt: str, size: str = "1024x1024",
                                      config_entry: str | None = None) -> Any:
        """§33 OpenAI image generation via openai_conversation.generate_image."""
        data = {"prompt": prompt, "size": size}
        if config_entry: data["config_entry"] = config_entry
        return await ws().call("call_service", domain="openai_conversation",
                                service="generate_image", service_data=data,
                                return_response=True)

    @tool(mcp)
    async def openai_ai_task_run(task_name: str, instructions: str,
                                  attachments: list | None = None,
                                  config_entry: str | None = None) -> Any:
        """§33 Run an AI task."""
        data: dict[str, Any] = {"task_name": task_name, "instructions": instructions}
        if attachments: data["attachments"] = attachments
        if config_entry: data["config_entry"] = config_entry
        return await ws().call("call_service", domain="ai_task",
                                service="generate_data", service_data=data,
                                return_response=True)

    @tool(mcp)
    async def anthropic_send(agent_id: str, text: str) -> Any:
        """§33 Anthropic conversation agent."""
        return await ws().call("conversation/process", text=text, agent_id=agent_id)

    @tool(mcp)
    async def google_generative_ai_send(agent_id: str, text: str) -> Any:
        """§33 Google generative AI conversation agent."""
        return await ws().call("conversation/process", text=text, agent_id=agent_id)

    @tool(mcp)
    async def ollama_send(agent_id: str, text: str) -> Any:
        """§33 Ollama conversation agent."""
        return await ws().call("conversation/process", text=text, agent_id=agent_id)

    return 6
