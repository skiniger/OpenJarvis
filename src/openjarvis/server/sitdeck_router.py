"""FastAPI router for /v1/sitdeck — SitDeck public API proxy endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from openjarvis.tools.sitdeck import SitDeckConnector

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/v1/sitdeck/health", tags=["sitdeck"])
async def sitdeck_health() -> dict[str, Any]:
    """Aggregate health check across all known SitDeck public endpoints."""
    connector = SitDeckConnector()
    try:
        results = await connector.health()
        return {"status": "ok", "sitdeck": results}
    except Exception as exc:
        logger.error("SitDeck health check failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        await connector.close()


@router.get("/v1/sitdeck/{endpoint}", tags=["sitdeck"])
async def sitdeck_endpoint(endpoint: str) -> dict[str, Any]:
    """Proxy a single SitDeck public endpoint by key."""
    connector = SitDeckConnector()
    try:
        result = await connector.fetch_endpoint(endpoint)
        if "error" in result:
            raise HTTPException(status_code=503, detail=result["error"])
        return {"status": "ok", "result": result}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("SitDeck endpoint %s query failed: %s", endpoint, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        await connector.close()
