"""Tests for the system_monitor tool."""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

from openjarvis.tools.system_monitor import SystemMonitorTool, _is_tabu_path


@pytest.fixture
def tool():
    return SystemMonitorTool()


@pytest.mark.skipif(
    pytest.importorskip("psutil") is None,
    reason="psutil not installed",
)
def test_metrics_returns_expected_keys(tool: SystemMonitorTool) -> None:
    result = tool.execute(action="metrics")
    assert result.success, result.content
    data = json.loads(result.content)
    assert "cpu" in data
    assert "memory" in data
    assert "disk" in data
    assert "timestamp" in data
    assert isinstance(data["cpu"]["percent"], (int, float))
    assert isinstance(data["memory"]["percent"], (int, float))


def test_metrics_without_psutil_reports_gracefully(tool: SystemMonitorTool) -> None:
    with mock.patch("openjarvis.tools.system_monitor.psutil", None):
        result = tool.execute(action="metrics")
        assert not result.success
        data = json.loads(result.content)
        assert "error" in data


def test_unknown_action_returns_error(tool: SystemMonitorTool) -> None:
    result = tool.execute(action="does_not_exist")
    assert not result.success
    data = json.loads(result.content)
    assert data["error"] == "Unknown action: does_not_exist"


def test_analyze_disk_returns_candidates(tool: SystemMonitorTool) -> None:
    result = tool.execute(action="analyze_disk")
    assert result.success, result.content
    data = json.loads(result.content)
    assert "candidates" in data
    assert "total_gb" in data
    assert isinstance(data["candidates"], list)
    assert isinstance(data["total_gb"], (int, float))


def test_is_tabu_path_protects_sensitive_directories() -> None:
    assert _is_tabu_path(Path("/System/Library"))
    assert _is_tabu_path(Path.home() / ".ssh")
    assert not _is_tabu_path(Path.home() / "Library" / "Caches" / "com.apple.dt.Xcode")


def test_clean_cache_respects_tabu_paths(tool: SystemMonitorTool) -> None:
    with mock.patch("openjarvis.tools.system_monitor._is_tabu_path", return_value=True):
        result = tool.execute(action="clean_cache")
        assert not result.success
        data = json.loads(result.content)
        for item in data.values():
            assert item["success"] is False
            assert "protected" in item["error"]


def test_spec_is_valid(tool: SystemMonitorTool) -> None:
    assert tool.spec.name == "system_monitor"
    assert "metrics" in tool.spec.parameters["properties"]["action"]["enum"]
    assert tool.spec.category == "system"
