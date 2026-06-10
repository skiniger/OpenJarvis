"""macOS native command tool — AppleScript, Finder, Notifications, System Info.

Provides macOS-specific operations through AppleScript and native subprocess
calls, integrated into the OpenJarvis tool registry.

Security boundaries:
- AppleScript blocks ``do shell script`` to prevent shell injection.
- Finder operations restrict paths under ``/System``, ``/private``, ``/dev``,
  and ``/Volumes``.
- Sudo is only available via AppleScript's ``with administrator privileges``,
  never direct ``sudo`` in subprocess.
"""

from __future__ import annotations

import json
import logging
import platform
import shlex
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from openjarvis.core.registry import ToolRegistry
from openjarvis.core.types import ToolResult
from openjarvis.tools._stubs import BaseTool, ToolSpec

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore[assignment]

LOGGER = logging.getLogger(__name__)

# Paths that Finder operations must not touch
_RESTRICTED_PATHS: set[str] = {
    "/System",
    "/private",
    "/dev",
    "/Volumes",
}

# AppleScript patterns that are blocked for security
_BLOCKED_APPLESCRIPT_PATTERNS: List[str] = [
    "do shell script",
]

_MAX_OUTPUT_BYTES = 102_400
_DEFAULT_TIMEOUT = 30


def _is_restricted_path(path: str) -> bool:
    """Check whether *path* is under a restricted root."""
    resolved = Path(path).expanduser().resolve()
    resolved_str = str(resolved)
    for restricted in _RESTRICTED_PATHS:
        if resolved_str.startswith(restricted):
            return True
    return False


def _contains_blocked_applescript(script: str) -> Optional[str]:
    """Return the first blocked pattern found, or None if safe."""
    lowered = script.lower()
    for pattern in _BLOCKED_APPLESCRIPT_PATTERNS:
        if pattern.lower() in lowered:
            return pattern
    return None


def _truncate(text: str, limit: int = _MAX_OUTPUT_BYTES) -> str:
    if len(text) > limit:
        return text[:limit] + "\n... (truncated)"
    return text


@ToolRegistry.register("macos_command")
class MacOSTool(BaseTool):
    """Execute native macOS commands via AppleScript and subprocess."""

    tool_id = "macos_command"
    is_local = True

    def __init__(self):
        self._spec = ToolSpec(
            name="macos_command",
            description=(
                "Execute native macOS commands including AppleScript, Finder control, "
                "system notifications, clipboard operations, volume control, text-to-speech, "
                "and system monitoring. Only available on macOS."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "applescript",
                            "finder",
                            "notification",
                            "system_info",
                            "clipboard",
                            "volume",
                            "say",
                        ],
                        "description": "The macOS operation to perform.",
                    },
                    "args": {
                        "type": "object",
                        "description": "Action-specific arguments.",
                    },
                    "sudo": {
                        "type": "boolean",
                        "default": False,
                        "description": "Run with administrator privileges (AppleScript only).",
                    },
                },
                "required": ["action"],
            },
            category="system",
            requires_confirmation=False,
            timeout_seconds=30.0,
            required_capabilities=["system:execute"],
        )

    @property
    def spec(self) -> ToolSpec:
        return self._spec

    def execute(self, **params: Any) -> ToolResult:
        action = params.get("action")
        if not action:
            return ToolResult(
                tool_name="macos_command",
                content="Missing required parameter: action.",
                success=False,
            )

        args: Dict[str, Any] = params.get("args") or {}
        sudo: bool = params.get("sudo", False)

        handlers = {
            "applescript": self._run_applescript,
            "finder": self._finder_action,
            "notification": self._send_notification,
            "system_info": self._get_system_info,
            "clipboard": self._clipboard_action,
            "volume": self._set_volume,
            "say": self._say_text,
        }

        handler = handlers.get(action)
        if handler is None:
            return ToolResult(
                tool_name="macos_command",
                content=f"Unknown action: {action}. Supported: {', '.join(handlers.keys())}.",
                success=False,
            )

        try:
            return handler(args=args, sudo=sudo)
        except Exception as exc:
            LOGGER.exception("macos_command %s failed", action)
            return ToolResult(
                tool_name="macos_command",
                content=f"Execution error: {exc}",
                success=False,
            )

    # ------------------------------------------------------------------
    # AppleScript
    # ------------------------------------------------------------------

    def _run_applescript(self, args: Dict[str, Any], sudo: bool) -> ToolResult:
        script = args.get("script", "")
        if not script:
            return ToolResult(
                tool_name="macos_command",
                content="Missing required argument: args.script.",
                success=False,
            )

        blocked = _contains_blocked_applescript(script)
        if blocked:
            return ToolResult(
                tool_name="macos_command",
                content=(
                    f"[SECURITY] AppleScript blocked: contains '{blocked}'."
                    f" Use the shell_exec tool for shell commands."
                ),
                success=False,
            )

        if sudo:
            wrapped = (
                f"do shell script {shlex.quote(f'osascript -e {shlex.quote(script)}')}"
                " with administrator privileges"
            )
            cmd = ["osascript", "-e", wrapped]
        else:
            cmd = ["osascript", "-e", script]

        return self._run_subprocess(cmd)

    # ------------------------------------------------------------------
    # Finder
    # ------------------------------------------------------------------

    def _finder_action(self, args: Dict[str, Any], sudo: bool) -> ToolResult:
        action = args.get("action", "")
        path = args.get("path", "")

        if action == "close":
            return self._run_applescript(
                args={"script": 'tell application "Finder" to close every window'},
                sudo=False,
            )

        if not path:
            return ToolResult(
                tool_name="macos_command",
                content="Missing required argument: args.path for finder action.",
                success=False,
            )

        if _is_restricted_path(path):
            return ToolResult(
                tool_name="macos_command",
                content=f"[SECURITY] Access to restricted path is not allowed: {path}",
                success=False,
            )

        resolved = str(Path(path).expanduser().resolve())

        if action == "open":
            return self._run_subprocess(["open", resolved])
        elif action == "reveal":
            return self._run_subprocess(["open", "-R", resolved])
        else:
            return ToolResult(
                tool_name="macos_command",
                content=f"Unknown finder action: {action}. Supported: open, reveal, close.",
                success=False,
            )

    # ------------------------------------------------------------------
    # Notification
    # ------------------------------------------------------------------

    def _send_notification(self, args: Dict[str, Any], sudo: bool) -> ToolResult:
        title = args.get("title", "Jarvis")
        message = args.get("message", "")
        if not message:
            return ToolResult(
                tool_name="macos_command",
                content="Missing required argument: args.message.",
                success=False,
            )

        script = f'display notification {shlex.quote(message)} with title {shlex.quote(title)}'
        return self._run_applescript(args={"script": script}, sudo=False)

    # ------------------------------------------------------------------
    # System Info
    # ------------------------------------------------------------------

    def _get_system_info(self, args: Dict[str, Any], sudo: bool) -> ToolResult:
        if psutil is None:
            return ToolResult(
                tool_name="macos_command",
                content="[ERROR] psutil is required for system_info. Install: uv pip install psutil",
                success=False,
            )

        try:
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            cpu_percent = psutil.cpu_percent(interval=1)

            data = {
                "os": platform.platform(),
                "processor": platform.processor(),
                "architecture": platform.machine(),
                "hostname": platform.node(),
                "python_version": platform.python_version(),
                "memory": {
                    "total_gb": round(mem.total / (1024 ** 3), 2),
                    "available_gb": round(mem.available / (1024 ** 3), 2),
                    "percent_used": mem.percent,
                },
                "disk": {
                    "total_gb": round(disk.total / (1024 ** 3), 2),
                    "used_gb": round(disk.used / (1024 ** 3), 2),
                    "free_gb": round(disk.free / (1024 ** 3), 2),
                    "percent_used": disk.percent,
                },
                "cpu_percent": cpu_percent,
                "cpu_count": psutil.cpu_count(logical=True),
                "boot_time": psutil.boot_time(),
            }

            # Battery (laptops only)
            battery = psutil.sensors_battery()
            if battery is not None:
                data["battery"] = {
                    "percent": battery.percent,
                    "power_plugged": battery.power_plugged,
                }

            return ToolResult(
                tool_name="macos_command",
                content=json.dumps(data, indent=2, default=str),
                success=True,
            )
        except Exception as exc:
            return ToolResult(
                tool_name="macos_command",
                content=f"System info collection failed: {exc}",
                success=False,
            )

    # ------------------------------------------------------------------
    # Clipboard
    # ------------------------------------------------------------------

    def _clipboard_action(self, args: Dict[str, Any], sudo: bool) -> ToolResult:
        action = args.get("action", "")
        if action == "set":
            text = args.get("text", "")
            if not text:
                return ToolResult(
                    tool_name="macos_command",
                    content="Missing required argument: args.text for clipboard set.",
                    success=False,
                )
            script = f"set the clipboard to {shlex.quote(text)}"
            return self._run_applescript(args={"script": script}, sudo=False)
        elif action == "get":
            script = "the clipboard as string"
            return self._run_applescript(args={"script": script}, sudo=False)
        else:
            return ToolResult(
                tool_name="macos_command",
                content=f"Unknown clipboard action: {action}. Supported: get, set.",
                success=False,
            )

    # ------------------------------------------------------------------
    # Volume
    # ------------------------------------------------------------------

    def _set_volume(self, args: Dict[str, Any], sudo: bool) -> ToolResult:
        level = args.get("level", 50)
        try:
            level = int(level)
        except (TypeError, ValueError):
            level = 50
        level = max(0, min(100, level))
        script = f"set volume output volume {level}"
        return self._run_applescript(args={"script": script}, sudo=False)

    # ------------------------------------------------------------------
    # Text-to-Speech
    # ------------------------------------------------------------------

    def _say_text(self, args: Dict[str, Any], sudo: bool) -> ToolResult:
        text = args.get("text", "")
        if not text:
            return ToolResult(
                tool_name="macos_command",
                content="Missing required argument: args.text for say.",
                success=False,
            )
        return self._run_subprocess(["say", text])

    # ------------------------------------------------------------------
    # Subprocess helper
    # ------------------------------------------------------------------

    def _run_subprocess(self, cmd: List[str], timeout: int = _DEFAULT_TIMEOUT) -> ToolResult:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                tool_name="macos_command",
                content=f"Command timed out after {timeout} seconds.",
                success=False,
                metadata={"timeout_used": timeout},
            )
        except FileNotFoundError as exc:
            return ToolResult(
                tool_name="macos_command",
                content=f"Command not found: {exc}",
                success=False,
            )
        except OSError as exc:
            return ToolResult(
                tool_name="macos_command",
                content=f"OS error: {exc}",
                success=False,
            )

        stdout = _truncate(result.stdout)
        stderr = _truncate(result.stderr)

        sections: list[str] = []
        if stdout:
            sections.append(f"=== STDOUT ===\n{stdout}")
        if stderr:
            sections.append(f"=== STDERR ===\n{stderr}")
        content = "\n".join(sections) if sections else "(no output)"

        return ToolResult(
            tool_name="macos_command",
            content=content,
            success=result.returncode == 0,
            metadata={"returncode": result.returncode},
        )


__all__ = ["MacOSTool"]
