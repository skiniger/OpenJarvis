"""Tests for the macos_command tool.

Tests mock subprocess/osascript and psutil to verify macOS-specific
operations without requiring a real macOS GUI session.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from openjarvis.core.registry import ToolRegistry
from openjarvis.core.types import ToolCall, ToolResult
from openjarvis.tools._stubs import ToolExecutor


class TestMacOSToolRegistration:
    """Verify the tool registers correctly in the OpenJarvis ecosystem."""

    def test_registered_in_tool_registry(self):
        import importlib
        import openjarvis.tools as tools_pkg

        sys.modules.pop("openjarvis.tools.macos_tool", None)
        importlib.reload(tools_pkg)

        assert ToolRegistry.contains("macos_command")

    def test_tool_id_matches_registry_key(self):
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        assert tool.tool_id == "macos_command"

    def test_spec_schema_valid(self):
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        spec = tool.spec
        assert spec.name == "macos_command"
        assert spec.category == "system"
        assert "action" in spec.parameters["properties"]
        assert "args" in spec.parameters["properties"]
        assert "sudo" in spec.parameters["properties"]
        assert "action" in spec.parameters["required"]
        assert spec.timeout_seconds == 30.0
        assert spec.requires_confirmation is False

    def test_to_openai_function(self):
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        fn = tool.to_openai_function()
        assert fn["type"] == "function"
        assert fn["function"]["name"] == "macos_command"
        assert "action" in fn["function"]["parameters"]["properties"]


class TestMacOSToolAppleScript:
    """AppleScript execution with security boundaries."""

    def test_applescript_success(self):
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        with patch(
            "openjarvis.tools.macos_tool.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="Finder window opened\n", stderr=""),
        ):
            result = tool.execute(action="applescript", args={"script": "tell application 'Finder' to activate"})
        assert result.success is True
        assert "Finder window opened" in result.content

    def test_applescript_failure(self):
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        with patch(
            "openjarvis.tools.macos_tool.subprocess.run",
            return_value=MagicMock(returncode=1, stdout="", stderr="Application not found"),
        ):
            result = tool.execute(action="applescript", args={"script": "tell application 'NonExistent' to activate"})
        assert result.success is False
        assert "Application not found" in result.content

    def test_applescript_blocks_do_shell_script(self):
        """Security: AppleScript containing 'do shell script' must be blocked."""
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        result = tool.execute(
            action="applescript",
            args={"script": "do shell script 'rm -rf /'"},
        )
        assert result.success is False
        assert "blocked" in result.content.lower() or "security" in result.content.lower()

    def test_applescript_allows_safe_scripts(self):
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        with patch(
            "openjarvis.tools.macos_tool.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="OK", stderr=""),
        ):
            result = tool.execute(
                action="applescript",
                args={"script": "display dialog 'Hello'"},
            )
        assert result.success is True

    def test_applescript_missing_script_param(self):
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        result = tool.execute(action="applescript", args={})
        assert result.success is False
        assert "script" in result.content.lower()


class TestMacOSToolFinder:
    """Finder operations with path restrictions."""

    def test_finder_open_success(self):
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        with patch(
            "openjarvis.tools.macos_tool.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="", stderr=""),
        ) as mock_run:
            result = tool.execute(
                action="finder",
                args={"action": "open", "path": "~/Documents"},
            )
        assert result.success is True
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert args[0][0] == "open"
        assert str(Path("~/Documents").expanduser()) in args[0]

    def test_finder_reveal(self):
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        with patch(
            "openjarvis.tools.macos_tool.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="", stderr=""),
        ) as mock_run:
            result = tool.execute(
                action="finder",
                args={"action": "reveal", "path": "~/Downloads"},
            )
        assert result.success is True
        args, _ = mock_run.call_args
        assert "-R" in args[0]

    def test_finder_restricted_system_path(self):
        """Security: Access to /System must be blocked."""
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        result = tool.execute(
            action="finder",
            args={"action": "open", "path": "/System/Library"},
        )
        assert result.success is False
        assert "restricted" in result.content.lower() or "security" in result.content.lower()

    def test_finder_restricted_private_path(self):
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        result = tool.execute(
            action="finder",
            args={"action": "open", "path": "/private/var"},
        )
        assert result.success is False

    def test_finder_close(self):
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        with patch(
            "openjarvis.tools.macos_tool.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="", stderr=""),
        ):
            result = tool.execute(action="finder", args={"action": "close"})
        assert result.success is True


class TestMacOSToolNotification:
    """macOS notification center integration."""

    def test_notification_send(self):
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        with patch(
            "openjarvis.tools.macos_tool.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="", stderr=""),
        ) as mock_run:
            result = tool.execute(
                action="notification",
                args={"title": "Jarvis", "message": "Task completed"},
            )
        assert result.success is True
        args, _ = mock_run.call_args
        assert "osascript" in args[0]
        assert "display notification" in args[0][2]


class TestMacOSToolClipboard:
    """Clipboard read/write."""

    def test_clipboard_set(self):
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        with patch(
            "openjarvis.tools.macos_tool.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="", stderr=""),
        ):
            result = tool.execute(
                action="clipboard",
                args={"action": "set", "text": "Hello from Jarvis"},
            )
        assert result.success is True

    def test_clipboard_get(self):
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        with patch(
            "openjarvis.tools.macos_tool.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="Clipboard content\n", stderr=""),
        ):
            result = tool.execute(
                action="clipboard",
                args={"action": "get"},
            )
        assert result.success is True
        assert "Clipboard content" in result.content


class TestMacOSToolVolume:
    """System volume control."""

    def test_volume_set_valid(self):
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        with patch(
            "openjarvis.tools.macos_tool.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="", stderr=""),
        ):
            result = tool.execute(
                action="volume",
                args={"level": 75},
            )
        assert result.success is True

    def test_volume_clamped_to_100(self):
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        with patch(
            "openjarvis.tools.macos_tool.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="", stderr=""),
        ) as mock_run:
            result = tool.execute(action="volume", args={"level": 150})
        assert result.success is True
        # Verify the script contains 100, not 150
        args, _ = mock_run.call_args
        assert "100" in args[0][2]

    def test_volume_clamped_to_0(self):
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        with patch(
            "openjarvis.tools.macos_tool.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="", stderr=""),
        ) as mock_run:
            result = tool.execute(action="volume", args={"level": -10})
        assert result.success is True
        args, _ = mock_run.call_args
        assert "0" in args[0][2]


class TestMacOSToolSay:
    """Text-to-Speech via 'say'."""

    def test_say_command(self):
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        with patch(
            "openjarvis.tools.macos_tool.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="", stderr=""),
        ) as mock_run:
            result = tool.execute(
                action="say",
                args={"text": "Hello world"},
            )
        assert result.success is True
        args, _ = mock_run.call_args
        assert args[0][0] == "say"
        assert args[0][1] == "Hello world"


class TestMacOSToolSystemInfo:
    """System monitoring via psutil."""

    def test_system_info_success(self):
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        # Mock psutil and platform modules
        mock_mem = MagicMock()
        mock_mem.total = 8 * 1024 ** 3
        mock_mem.available = 2 * 1024 ** 3
        mock_mem.percent = 75.0

        mock_disk = MagicMock()
        mock_disk.total = 256 * 1024 ** 3
        mock_disk.used = 100 * 1024 ** 3
        mock_disk.free = 156 * 1024 ** 3
        mock_disk.percent = 39.0

        mock_battery = MagicMock()
        mock_battery.percent = 85.0
        mock_battery.power_plugged = True

        with patch("openjarvis.tools.macos_tool.psutil.virtual_memory", return_value=mock_mem), \
             patch("openjarvis.tools.macos_tool.psutil.disk_usage", return_value=mock_disk), \
             patch("openjarvis.tools.macos_tool.psutil.cpu_percent", return_value=25.0), \
             patch("openjarvis.tools.macos_tool.psutil.cpu_count", return_value=8), \
             patch("openjarvis.tools.macos_tool.psutil.boot_time", return_value=1_700_000_000), \
             patch("openjarvis.tools.macos_tool.psutil.sensors_battery", return_value=mock_battery), \
             patch("openjarvis.tools.macos_tool.platform.platform", return_value="macOS-14.0-arm64"), \
             patch("openjarvis.tools.macos_tool.platform.processor", return_value="arm"), \
             patch("openjarvis.tools.macos_tool.platform.machine", return_value="arm64"), \
             patch("openjarvis.tools.macos_tool.platform.node", return_value="test-mac"), \
             patch("openjarvis.tools.macos_tool.platform.python_version", return_value="3.13.0"):
            result = tool.execute(action="system_info", args={})

        assert result.success is True
        data = json.loads(result.content)
        assert data["os"] == "macOS-14.0-arm64"
        assert data["processor"] == "arm"
        assert data["memory"]["total_gb"] == 8.0
        assert data["memory"]["percent_used"] == 75.0
        assert data["disk"]["total_gb"] == 256.0
        assert data["cpu_percent"] == 25.0
        assert data["battery"]["percent"] == 85.0

    def test_system_info_psutil_missing(self):
        """Graceful degradation when psutil is not installed."""
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        with patch.dict(sys.modules, {"psutil": None}):
            with patch("builtins.__import__", side_effect=lambda name, *args, **kwargs: None if name == "psutil" else __import__(name, *args, **kwargs)):
                # Actually, the import is at module level. Let's simulate by patching the module attribute.
                pass

        # Simpler approach: patch the module's psutil reference directly
        import openjarvis.tools.macos_tool as macos_module
        original_psutil = getattr(macos_module, "psutil", None)
        try:
            macos_module.psutil = None  # type: ignore[attr-defined]
            result = tool.execute(action="system_info", args={})
            assert result.success is False
            assert "psutil" in result.content.lower()
        finally:
            if original_psutil is not None:
                macos_module.psutil = original_psutil  # type: ignore[attr-defined]


class TestMacOSToolUnknownAction:
    """Error handling for unsupported actions."""

    def test_unknown_action(self):
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        result = tool.execute(action="nonexistent", args={})
        assert result.success is False
        assert "unknown" in result.content.lower()

    def test_missing_action(self):
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        result = tool.execute(args={})
        assert result.success is False
        assert "action" in result.content.lower()


class TestMacOSToolViaToolExecutor:
    """Integration with the OpenJarvis ToolExecutor dispatch engine."""

    def test_executor_dispatch(self):
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        executor = ToolExecutor([tool])
        call = ToolCall(
            id="1",
            name="macos_command",
            arguments=json.dumps({"action": "say", "args": {"text": "test"}}),
        )
        with patch(
            "openjarvis.tools.macos_tool.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="", stderr=""),
        ):
            result = executor.execute(call)
        assert result.success is True

    def test_executor_unknown_tool(self):
        """Verify the executor rejects unknown tools gracefully."""
        from openjarvis.tools.macos_tool import MacOSTool

        tool = MacOSTool()
        executor = ToolExecutor([tool])
        call = ToolCall(
            id="1",
            name="nonexistent_tool",
            arguments=json.dumps({"action": "say", "args": {"text": "test"}}),
        )
        result = executor.execute(call)
        assert result.success is False
        assert "Unknown tool" in result.content
