import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from openjarvis.server import osint_router
from openjarvis.server import osint_store

@pytest.fixture
def client():
    # initialize fresh store
    osint_store._store = osint_store.OsintStore(persist_path=None)
    app = FastAPI()
    app.include_router(osint_router.router)
    yield TestClient(app)
    # cleanup
    osint_store._store = osint_store.OsintStore(persist_path=None)


def test_update_schedule_target(client):
    osint_store._store.create_schedule(
        "anonymous",
        target="old.com",
        modules=["dns"],
        interval_minutes=60,
    )
    s = osint_store._store.list_schedules("anonymous")[0]

    resp = client.patch(f"/v1/osint/schedule/{s['id']}", json={"target": "new.com"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["target"] == "new.com"
    assert data["modules"] == ["dns"]
    assert data["interval_minutes"] == 60


def test_update_schedule_modules(client):
    osint_store._store.create_schedule(
        "anonymous",
        target="example.com",
        modules=["dns"],
        interval_minutes=60,
    )
    s = osint_store._store.list_schedules("anonymous")[0]

    resp = client.patch(
        f"/v1/osint/schedule/{s['id']}",
        json={"modules": ["dns", "whois"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["modules"] == ["dns", "whois"]


def test_update_schedule_interval(client):
    osint_store._store.create_schedule(
        "anonymous",
        target="example.com",
        modules=["dns"],
        interval_minutes=60,
    )
    s = osint_store._store.list_schedules("anonymous")[0]

    resp = client.patch(
        f"/v1/osint/schedule/{s['id']}",
        json={"interval_minutes": 120},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["interval_minutes"] == 120


def test_update_schedule_not_found(client):
    resp = client.patch(
        "/v1/osint/schedule/nonexistent",
        json={"target": "new.com"},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Schedule not found"


def test_update_schedule_partial(client):
    osint_store._store.create_schedule(
        "anonymous",
        target="example.com",
        modules=["dns"],
        interval_minutes=60,
    )
    s = osint_store._store.list_schedules("anonymous")[0]

    resp = client.patch(
        f"/v1/osint/schedule/{s['id']}",
        json={"target": "updated.com", "interval_minutes": 30},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["target"] == "updated.com"
    assert data["interval_minutes"] == 30
    assert data["modules"] == ["dns"]
