"""Release metadata checks for the Home Assistant add-on."""

import json
from pathlib import Path

import pytest
import yaml
from packaging.requirements import Requirement


def test_addon_manifest_has_no_duplicate_keys():
    manifest_path = Path(__file__).resolve().parents[1] / "config.yaml"
    manifest = yaml.compose(manifest_path.read_text(encoding="utf-8"))
    keys = [key.value for key, _value in manifest.value]

    assert len(keys) == len(set(keys)), "Duplicate manifest keys override release settings"


def test_mcp_dependency_keeps_the_fastmcp_v1_api():
    requirements_path = Path(__file__).resolve().parents[1] / "requirements.txt"
    dependencies = [
        Requirement(line)
        for line in requirements_path.read_text(encoding="utf-8").splitlines()
        if line.startswith("mcp>=")
    ]

    assert dependencies
    for dependency in dependencies:
        assert "1.4.1" in dependency.specifier
        assert "2.0.0" not in dependency.specifier


@pytest.mark.asyncio
async def test_release_metadata_is_consistent():
    from app.transport import handle_info

    addon = Path(__file__).resolve().parents[1]
    manifest = yaml.safe_load((addon / "config.yaml").read_text(encoding="utf-8"))
    repository = yaml.safe_load((addon.parent / "repository.yaml").read_text(encoding="utf-8"))
    changelog = (addon / "CHANGELOG.md").read_text(encoding="utf-8")
    response = await handle_info(None)

    assert json.loads(response.body)["version"] == manifest["version"]
    assert (
        next(line for line in changelog.splitlines() if line.startswith("## ")).split()[1]
        == manifest["version"]
    )
    assert (
        repository["url"]
        == manifest["url"]
        == "https://github.com/ITSpecialist111/HASS_MCP_OpenClaw"
    )
