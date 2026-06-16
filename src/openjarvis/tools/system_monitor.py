"""System monitoring tool for OpenJarvis agents.

Collects CPU, RAM, disk and (on macOS) GPU metrics via psutil and exposes
maintenance actions such as cache cleanup and disk analysis. All destructive
operations are opt-in and bounded to well-known cache directories.
"""

from __future__ import annotations

import json
import logging
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict

from openjarvis.core.registry import ToolRegistry
from openjarvis.core.types import ToolResult
from openjarvis.tools._stubs import BaseTool, ToolSpec

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore[assignment]

LOGGER = logging.getLogger(__name__)

# Well-known cache directories that are safe to clear on macOS.
_CACHE_TARGETS = {
    "browser_chrome": Path.home() / "Library" / "Application Support" / "Google" / "Chrome" / "Default" / "Cache",
    "browser_firefox": Path.home() / "Library" / "Application Support" / "Firefox" / "Profiles",
    "npm": Path.home() / ".npm",
    "xcode": Path.home() / "Library" / "Caches" / "com.apple.dt.Xcode",
}

# Directories analysed by the disk-analysis action.
_DISK_ANALYSIS_TARGETS = [
    ("App Caches", Path.home() / "Library" / "Caches"),
    ("System Logs", Path.home() / "Library" / "Logs"),
    ("npm Cache", Path.home() / ".npm"),
    ("Xcode Archives", Path.home() / "Library" / "Developer" / "Xcode" / "Archives"),
    ("Xcode DerivedData", Path.home() / "Library" / "Developer" / "Xcode" / "DerivedData"),
    ("iOS Simulators", Path.home() / "Library" / "Developer" / "CoreSimulator"),
    ("User Cache", Path.home() / ".cache"),
]

# Paths that must never be touched by cleanup or analysis actions.
_TABU_PATHS: set[str] = {
    "/System",
    "/private",
    "/dev",
    "/Volumes",
    str(Path.home() / ".ssh"),
    str(Path.home() / ".gnupg"),
    str(Path.home() / ".config"),
    str(Path.home() / "Documents"),
    str(Path.home() / "Pictures"),
    str(Path.home() / ".Trash"),
}


def _is_tabu_path(path: Path) -> bool:
    """Return True if *path* is under a protected root."""
    try:
        resolved = path.expanduser().resolve()
    except (OSError, RuntimeError):
        return True
    resolved_str = str(resolved)
    for tabu in _TABU_PATHS:
        if resolved_str.startswith(tabu):
            return True
    return False


def _collect_metrics() -> Dict[str, Any]:
    """Return live system metrics."""
    if psutil is None:
        raise RuntimeError("psutil is required for system monitoring")

    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    cpu_percent = psutil.cpu_percent(interval=0.1)
    load_avg = None
    try:
        load_avg = psutil.getloadavg()
    except (AttributeError, OSError):
        pass

    data: Dict[str, Any] = {
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "hostname": platform.node(),
        "cpu": {
            "percent": cpu_percent,
            "count_logical": psutil.cpu_count(logical=True),
            "count_physical": psutil.cpu_count(logical=False),
            "load_avg_1min": load_avg[0] if load_avg else None,
        },
        "memory": {
            "total_gb": round(mem.total / (1024 ** 3), 2),
            "available_gb": round(mem.available / (1024 ** 3), 2),
            "used_gb": round(mem.used / (1024 ** 3), 2),
            "percent": mem.percent,
        },
        "disk": {
            "total_gb": round(disk.total / (1024 ** 3), 2),
            "used_gb": round(disk.used / (1024 ** 3), 2),
            "free_gb": round(disk.free / (1024 ** 3), 2),
            "percent": disk.percent,
        },
        "gpu": _gpu_snapshot(),
        "timestamp": _now_iso(),
    }

    battery = psutil.sensors_battery()
    if battery is not None:
        data["battery"] = {
            "percent": battery.percent,
            "power_plugged": battery.power_plugged,
        }

    return data


def _gpu_snapshot() -> Dict[str, Any] | None:
    """Best-effort GPU snapshot. Only macOS is supported; returns None elsewhere."""
    if platform.system() != "Darwin":
        return None
    try:
        result = subprocess.run(
            ["ioreg", "-r", "-c", "AppleM1GPU"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return {
            "vendor": "apple",
            "raw_sample_length": len(result.stdout),
            "note": "GPU monitoring on Apple Silicon is experimental",
        }
    except Exception as exc:
        return {"vendor": "apple", "error": str(exc)}


def _now_iso() -> str:
    """Return current UTC timestamp as ISO string."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def _analyze_disk() -> Dict[str, Any]:
    """Return disk usage candidates sorted by size."""
    candidates: list[Dict[str, Any]] = []
    for label, target in _DISK_ANALYSIS_TARGETS:
        if _is_tabu_path(target):
            continue
        try:
            size_bytes = shutil.disk_usage(target).used if target.exists() else 0
            size_gb = round(size_bytes / (1024 ** 3), 2)
            if size_gb > 0:
                candidates.append({"label": label, "path": str(target), "size_gb": size_gb})
        except Exception as exc:
            LOGGER.debug("Disk analysis skipped for %s: %s", target, exc)

    candidates.sort(key=lambda item: item["size_gb"], reverse=True)
    total_gb = round(sum(item["size_gb"] for item in candidates), 2)
    return {"candidates": candidates, "total_gb": total_gb}


def _clean_cache() -> Dict[str, Any]:
    """Clear known caches and return per-target success flags."""
    result: Dict[str, Any] = {}

    for name, target in _CACHE_TARGETS.items():
        if _is_tabu_path(target):
            result[name] = {"success": False, "error": "protected path"}
            continue
        try:
            if name == "browser_firefox":
                # Firefox stores cache under each profile's cache2 directory.
                cleared = 0
                if target.exists():
                    for profile in target.iterdir():
                        cache2 = profile / "cache2"
                        if cache2.exists():
                            _rm_tree(cache2)
                            cleared += 1
                result[name] = {"success": cleared > 0 or not target.exists()}
            else:
                if target.exists():
                    _rm_tree(target)
                result[name] = {"success": True}
        except Exception as exc:
            LOGGER.warning("Cache cleanup failed for %s: %s", name, exc)
            result[name] = {"success": False, "error": str(exc)}

    return result


def _rm_tree(path: Path) -> None:
    """Remove a file or directory tree, raising on protected paths."""
    if _is_tabu_path(path):
        raise PermissionError(f"Refusing to remove protected path: {path}")
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    elif path.is_file() or path.is_symlink():
        path.unlink(missing_ok=True)


@ToolRegistry.register("system_monitor")
class SystemMonitorTool(BaseTool):
    """Live system metrics and bounded maintenance actions."""

    tool_id = "system_monitor"
    is_local = True

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="system_monitor",
            description=(
                "Monitor the local host (CPU, RAM, disk, GPU) and run safe "
                "maintenance actions such as cache cleanup and disk analysis. "
                "All destructive operations are limited to known cache directories."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["metrics", "clean_cache", "analyze_disk"],
                        "description": "Operation to perform.",
                    },
                },
                "required": ["action"],
            },
            category="system",
            requires_confirmation=False,
            timeout_seconds=30.0,
            required_capabilities=["system:monitor"],
        )

    def execute(self, action: str = "", **kwargs: Any) -> ToolResult:
        if action == "metrics":
            try:
                data = _collect_metrics()
                return ToolResult(
                    tool_name="system_monitor",
                    content=json.dumps(data, indent=2, default=str),
                    success=True,
                )
            except Exception as exc:
                LOGGER.exception("system_monitor metrics failed")
                return ToolResult(
                    tool_name="system_monitor",
                    content=json.dumps({"error": str(exc)}),
                    success=False,
                )

        if action == "clean_cache":
            try:
                data = _clean_cache()
                success = all(v.get("success", False) for v in data.values())
                return ToolResult(
                    tool_name="system_monitor",
                    content=json.dumps(data, indent=2, default=str),
                    success=success,
                )
            except Exception as exc:
                LOGGER.exception("system_monitor clean_cache failed")
                return ToolResult(
                    tool_name="system_monitor",
                    content=json.dumps({"error": str(exc)}),
                    success=False,
                )

        if action == "analyze_disk":
            try:
                data = _analyze_disk()
                return ToolResult(
                    tool_name="system_monitor",
                    content=json.dumps(data, indent=2, default=str),
                    success=True,
                )
            except Exception as exc:
                LOGGER.exception("system_monitor analyze_disk failed")
                return ToolResult(
                    tool_name="system_monitor",
                    content=json.dumps({"error": str(exc)}),
                    success=False,
                )

        return ToolResult(
            tool_name="system_monitor",
            content=json.dumps({"error": f"Unknown action: {action}"}),
            success=False,
        )


__all__ = ["SystemMonitorTool"]
