"""Monitoring router for OpenJarvis server.

Exposes live system metrics and bounded maintenance actions. Endpoints are
public by design so the dashboard can display host status without requiring
an API key; destructive actions remain read-only diagnostics.
"""

from __future__ import annotations

import logging
from typing import Any

import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from openjarvis.tools.system_monitor import SystemMonitorTool

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/monitoring", tags=["monitoring"])


def _run_tool(action: str) -> dict[str, Any]:
    """Execute a system_monitor tool action and return its parsed payload."""
    tool = SystemMonitorTool()
    result = tool.execute(action=action)
    try:
        payload = json.loads(result.content) if result.content else {}
    except Exception as exc:
        logger.error("Monitoring tool returned non-JSON: %s", exc)
        raise HTTPException(status_code=500, detail="Invalid monitoring response")
    if not result.success:
        detail = payload.get("error", "Monitoring action failed")
        raise HTTPException(status_code=500, detail=detail)
    return payload


@router.get("/metrics")
async def monitoring_metrics() -> dict[str, Any]:
    """Return live CPU, RAM, disk and GPU metrics for the host."""
    return _run_tool("metrics")


@router.post("/analyze-disk")
async def monitoring_analyze_disk() -> dict[str, Any]:
    """Return cleanable disk candidates sorted by size."""
    return _run_tool("analyze_disk")


@router.post("/clean-cache")
async def monitoring_clean_cache() -> dict[str, Any]:
    """Clear known cache directories (browser, npm, Xcode).

    Requires the ``system:monitor`` capability and is destructive; it is kept
    behind a POST to make accidental refresh-triggered cleanup impossible.
    """
    return _run_tool("clean_cache")


__all__ = ["router"]
