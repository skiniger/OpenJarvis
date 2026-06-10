"""Integration tests for the macos_command skill.

Validates skill manifest loading, ToolExecutor dispatch, and SkillManager
catalog integration.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from openjarvis.core.events import EventBus
from openjarvis.core.registry import SkillRegistry, ToolRegistry
from openjarvis.core.types import ToolCall
from openjarvis.skills.loader import load_skill_directory
from openjarvis.skills.manager import SkillManager
from openjarvis.skills.tool_adapter import SkillTool
from openjarvis.tools._stubs import ToolExecutor


SKILL_DIR = Path(__file__).parent.parent.parent / "skills" / "macos_command"


class TestMacOSSkillManifest:
    """Skill manifest loading and validation."""

    def test_skill_directory_exists(self):
        assert SKILL_DIR.exists(), f"Skill directory not found: {SKILL_DIR}"

    def test_skill_toml_loads(self):
        manifest = load_skill_directory(SKILL_DIR)
        assert manifest.name == "macos_command"
        assert manifest.version == "1.0.0"
        assert "macos" in manifest.description.lower()
        assert "system:execute" in manifest.required_capabilities

    def test_skill_has_steps(self):
        manifest = load_skill_directory(SKILL_DIR)
        assert len(manifest.steps) >= 1
        assert manifest.steps[0].tool_name == "macos_command"

    def test_skill_markdown_content(self):
        manifest = load_skill_directory(SKILL_DIR)
        assert manifest.markdown_content
        assert "macOS" in manifest.markdown_content or "applescript" in manifest.markdown_content.lower()

    def test_skill_user_invocable(self):
        manifest = load_skill_directory(SKILL_DIR)
        assert manifest.user_invocable is True

    def test_skill_tags(self):
        manifest = load_skill_directory(SKILL_DIR)
        assert "macos" in manifest.tags
        assert "system" in manifest.tags


class TestMacOSSkillExecution:
    """End-to-end skill execution via SkillManager and ToolExecutor."""

    def test_skill_manager_discovery(self):
        bus = EventBus()
        manager = SkillManager(bus)
        manager.discover([SKILL_DIR.parent])

        assert "macos_command" in manager.skill_names()

    def test_skill_manager_catalog_xml(self):
        bus = EventBus()
        manager = SkillManager(bus)
        manager.discover([SKILL_DIR.parent])

        catalog = manager.get_catalog_xml()
        assert "macos_command" in catalog
        assert "macos" in catalog.lower()

    def test_skill_as_tool_via_tool_executor(self):
        from openjarvis.tools.macos_tool import MacOSTool

        bus = EventBus(record_history=True)
        manager = SkillManager(bus)
        manager.discover([SKILL_DIR.parent])

        macos_tool = MacOSTool()
        skill_tools = manager.get_skill_tools()
        all_tools = [macos_tool] + skill_tools

        executor = ToolExecutor(all_tools, bus=bus)
        manager.set_tool_executor(executor)

        # Execute the raw macos_command tool directly
        call = ToolCall(
            id="1",
            name="macos_command",
            arguments=json.dumps({
                "action": "notification",
                "args": {"title": "Test", "message": "Hello"},
            }),
        )

        with patch(
            "openjarvis.tools.macos_tool.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="", stderr=""),
        ):
            result = executor.execute(call)

        assert result.success is True

        # Verify events were emitted
        start_events = [e for e in bus.history if e.event_type.name == "TOOL_CALL_START"]
        end_events = [e for e in bus.history if e.event_type.name == "TOOL_CALL_END"]
        assert len(start_events) >= 1
        assert len(end_events) >= 1

    def test_skill_execute_via_manager(self):
        from openjarvis.tools.macos_tool import MacOSTool

        bus = EventBus()
        manager = SkillManager(bus)
        manager.discover([SKILL_DIR.parent])

        macos_tool = MacOSTool()
        skill_tools = manager.get_skill_tools()
        all_tools = [macos_tool] + skill_tools
        executor = ToolExecutor(all_tools, bus=bus)
        manager.set_tool_executor(executor)

        with patch(
            "openjarvis.tools.macos_tool.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="Done", stderr=""),
        ):
            result = manager.execute("macos_command", context={"action": "say", "args": {"text": "test"}})

        assert result is not None

    def test_skill_tool_openai_format(self):
        from openjarvis.tools.macos_tool import MacOSTool

        bus = EventBus()
        manager = SkillManager(bus)
        manager.discover([SKILL_DIR.parent])

        macos_tool = MacOSTool()
        skill_tools = manager.get_skill_tools()
        all_tools = [macos_tool] + skill_tools
        executor = ToolExecutor(all_tools, bus=bus)

        openai_tools = executor.get_openai_tools()
        names = [t["function"]["name"] for t in openai_tools]
        assert "macos_command" in names
