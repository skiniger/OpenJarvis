"""Tests for the Landhaus Bavaria FastAPI router."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from openjarvis.server.landhaus_router import router as landhaus_router


@pytest.fixture
def client() -> TestClient:
    """Create a TestClient with only the landhaus router mounted."""
    app = FastAPI()
    app.include_router(landhaus_router)
    return TestClient(app)


# ---------------------------------------------------------------------------
# /v1/landhaus/health
# ---------------------------------------------------------------------------

class TestLandhausHealth:
    """Tests for GET /v1/landhaus/health."""

    def test_health_ok(self, client: TestClient) -> None:
        mock_connector = AsyncMock()
        mock_connector.health.return_value = {
            "website": {"status": "up", "status_code": 200},
            "deskline": {"status": "up"},
            "ical": {"status": "up", "content_length": 1234},
            "vercel": {"status": "up", "latest_state": "READY"},
        }
        mock_connector.close = AsyncMock()

        with patch(
            "openjarvis.server.landhaus_router.LandhausBavariaConnector",
            return_value=mock_connector,
        ):
            response = client.get("/v1/landhaus/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        sources = data["sources"]
        assert "website" in sources
        assert "deskline" in sources
        assert "ical" in sources
        assert "vercel" in sources
        mock_connector.close.assert_awaited_once()

    def test_health_connector_exception(self, client: TestClient) -> None:
        mock_connector = AsyncMock()
        mock_connector.health.side_effect = RuntimeError("boom")
        mock_connector.close = AsyncMock()

        with patch(
            "openjarvis.server.landhaus_router.LandhausBavariaConnector",
            return_value=mock_connector,
        ):
            response = client.get("/v1/landhaus/health")

        assert response.status_code == 500
        assert "boom" in response.json()["detail"]
        mock_connector.close.assert_awaited_once()


# ---------------------------------------------------------------------------
# /v1/landhaus/availability
# ---------------------------------------------------------------------------

class TestLandhausAvailability:
    """Tests for GET /v1/landhaus/availability."""

    def test_availability_ok(self, client: TestClient) -> None:
        mock_connector = AsyncMock()
        mock_connector.room_availability.return_value = {
            "available_rooms": [
                {"room": "Doppelzimmer", "available": True},
                {"room": "Einzelzimmer", "available": False},
            ]
        }
        mock_connector.close = AsyncMock()

        with patch(
            "openjarvis.server.landhaus_router.LandhausBavariaConnector",
            return_value=mock_connector,
        ):
            response = client.get(
                "/v1/landhaus/availability",
                params={"date_from": "2026-06-01", "date_to": "2026-06-10"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "available_rooms" in data
        mock_connector.room_availability.assert_awaited_once_with("2026-06-01", "2026-06-10")
        mock_connector.close.assert_awaited_once()

    def test_availability_connector_error(self, client: TestClient) -> None:
        mock_connector = AsyncMock()
        mock_connector.room_availability.return_value = {"error": "Deskline proxy unreachable"}
        mock_connector.close = AsyncMock()

        with patch(
            "openjarvis.server.landhaus_router.LandhausBavariaConnector",
            return_value=mock_connector,
        ):
            response = client.get(
                "/v1/landhaus/availability",
                params={"date_from": "2026-06-01", "date_to": "2026-06-10"},
            )

        assert response.status_code == 503
        assert "Deskline proxy unreachable" in response.json()["detail"]
        mock_connector.close.assert_awaited_once()

    def test_availability_connector_exception(self, client: TestClient) -> None:
        mock_connector = AsyncMock()
        mock_connector.room_availability.side_effect = RuntimeError("network down")
        mock_connector.close = AsyncMock()

        with patch(
            "openjarvis.server.landhaus_router.LandhausBavariaConnector",
            return_value=mock_connector,
        ):
            response = client.get(
                "/v1/landhaus/availability",
                params={"date_from": "2026-06-01", "date_to": "2026-06-10"},
            )

        assert response.status_code == 500
        assert "network down" in response.json()["detail"]
        mock_connector.close.assert_awaited_once()
