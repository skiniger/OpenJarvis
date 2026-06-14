"""Tests for OSINT report export endpoint."""

from __future__ import annotations

import openjarvis.server.osint_store as store_mod
import pytest


@pytest.fixture
def client():
    """FastAPI TestClient with OSINT router."""
    pytest.importorskip("fastapi")
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from openjarvis.server.osint_router import router

    app = FastAPI()
    app.include_router(router)
    yield TestClient(app)


def test_report_json(client) -> None:
    store = store_mod.OsintStore()
    store.save_scan("anonymous", "example.com", ["dns"], {"reachable": True}, {"errors": 0})
    store.save_exec("anonymous", "nmap", "127.0.0.1", "open ports", True, {"version": "7.94"})

    store_mod._store = store
    try:
        response = client.get("/v1/osint/report")
    finally:
        store_mod._store = None

    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "json"
    assert data["filename"].endswith(".json")
    assert data["data"]["user_id"] == "anonymous"
    assert data["data"]["summary"]["total_scans"] == 1
    assert data["data"]["summary"]["total_execs"] == 1
    assert len(data["data"]["history"]) == 2
    assert "generated_at" in data["data"]


def test_report_markdown(client) -> None:
    store = store_mod.OsintStore()
    store.save_scan("anonymous", "example.com", ["dns"], {"reachable": True}, {"errors": 0})
    store.save_exec("anonymous", "nmap", "127.0.0.1", "open ports", True, {"version": "7.94"})

    store_mod._store = store
    try:
        response = client.get("/v1/osint/report?fmt=markdown")
    finally:
        store_mod._store = None

    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "markdown"
    assert data["filename"].endswith(".md")
    assert data["content"].startswith("# OSINT Report")
    assert "Total Scans: 1" in data["content"]
    assert "example.com" in data["content"]


def test_report_empty(client) -> None:
    store = store_mod.OsintStore()

    store_mod._store = store
    try:
        response = client.get("/v1/osint/report")
    finally:
        store_mod._store = None

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["summary"]["total_scans"] == 0
    assert data["data"]["alerts"] == []
    assert data["data"]["schedules"] == []
    assert data["data"]["favorites"] == []


def test_report_with_alerts_and_schedules(client) -> None:
    store = store_mod.OsintStore()
    store.save_scan("anonymous", "example.com", ["dns"], {"reachable": True}, {"errors": 0})
    store.create_schedule("anonymous", "example.com", ["dns"], 60)

    store_mod._store = store
    try:
        response = client.get("/v1/osint/report")
    finally:
        store_mod._store = None

    data = response.json()
    assert data["data"]["schedules"][0]["target"] == "example.com"
    assert data["data"]["schedules"][0]["interval_minutes"] == 60
