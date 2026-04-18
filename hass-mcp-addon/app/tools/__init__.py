"""Tool registration package. Each module exposes register(mcp)."""
from __future__ import annotations

import importlib
import logging

logger = logging.getLogger(__name__)

_MODULES = [
    "raw",            # §41 — escape hatches first so others can lean on them
    "entities",       # §2
    "devices",        # §3
    "config_entries", # §4
    "areas",          # §5
    "supervisor",     # §6
    "automations",    # §7
    "dashboards",     # §8
    "frontend",       # §9
    "recorder",       # §10
    "energy",         # §11
    "templates",      # §12
    "events",         # §13
    "users",          # §14
    "mqtt",           # §15
    "radios",         # §16
    "esphome",        # §17
    "frigate",        # §18
    "media",          # §19
    "notify",         # §20
    "mobile",         # §21
    "tags",           # §22
    "calendar_todo",  # §23-24
    "files",          # §25
    "database",       # §26
    "network",        # §27
    "shell_tools",    # §28
    "docker_tools",   # §29
    "hacs",           # §30
    "cloud",          # §31
    "voice",          # §32
    "ai",             # §33
    "octopus",        # §34
    "energy_vendors", # §35
    "observability",  # §36
    "translations",   # §37
    "search",         # §38
    "bulk",           # §39
    "streams",        # §40
    # ---- Part II: God Mode delta (§§50–63) ----
    "persistence",    # §50
    "infra",          # §51
    "saas",           # §52
    "hardware",       # §53
    "identity",       # §54
    "physical",       # §55
    "forensics",      # §56
    "selfmod",        # §57
    "multimodal",     # §58
    "agency",         # §59
    "legal_edge",     # §60
    "audit",          # convenience: high-level audit + cleanup
]


def register_all(mcp) -> int:
    count = 0
    for mod_name in _MODULES:
        try:
            mod = importlib.import_module(f".{mod_name}", __name__)
            if hasattr(mod, "register"):
                added = mod.register(mcp)
                count += added or 0
                logger.info("Registered %s (%s tools)", mod_name, added)
        except Exception:
            logger.exception("Failed to register tool module %s", mod_name)
    return count
