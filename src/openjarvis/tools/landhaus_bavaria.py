"""LandhausBavariaConnector — read-only health and data access tool.

Queries approved external systems for the Landhaus Bavaria domain:
- Deskline WebClient (room availability)
- Booking.com iCal (sync status)
- Vercel API (deployment status)
- Website health and content scraping (landhausbavaria.de)

Credentials are read from environment variables; they are never logged.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List

import httpx
from bs4 import BeautifulSoup

from openjarvis.core.registry import ToolRegistry
from openjarvis.core.types import ToolResult
from openjarvis.tools._stubs import BaseTool, ToolSpec

logger = logging.getLogger(__name__)

_DESKLINE_BASE = os.environ.get("DESKLINE_BASE_URL", "https://webclient4.deskline.net")
_VERCEL_TOKEN = os.environ.get("VERCEL_API_TOKEN")
_ICAL_URL = os.environ.get("BOOKINGCOM_ICAL_URL")
_WEBSITE_URL = os.environ.get("LANDHAUS_WEBSITE", "https://www.landhausbavaria.de")

_WEEKDAY_SPECIALS = [
    "Bavaria Burgertag",
    "Ripperl-Tag",
    "Großer Schnitzeltag",
    "Haxn Tag",
    "Krustenbraten",
]


class LandhausBavariaConnector:
    """Lightweight connector for approved Landhaus Bavaria data sources."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=15.0)

    async def health(self) -> Dict[str, Any]:
        """Run health checks against all configured data sources."""
        results: Dict[str, Any] = {}

        # Website health + content scrape
        try:
            resp = await self._client.get(_WEBSITE_URL, follow_redirects=True)
            results["website"] = {
                "status": "up" if resp.status_code == 200 else "degraded",
                "status_code": resp.status_code,
            }
            if resp.status_code == 200:
                try:
                    results["website"]["data"] = _scrape_website(resp.text, _WEBSITE_URL)
                except Exception as exc:
                    logger.warning("Website scrape failed: %s", exc)
                    results["website"]["scrape_error"] = str(exc)
        except Exception as exc:
            results["website"] = {"status": "down", "error": str(exc)}

        # Deskline proxy
        if os.environ.get("DESKLINE_PROXY_URL"):
            try:
                resp = await self._client.get(os.environ["DESKLINE_PROXY_URL"] + "/health")
                results["deskline"] = {"status": "up" if resp.status_code == 200 else "degraded"}
            except Exception as exc:
                results["deskline"] = {"status": "down", "error": str(exc)}
        else:
            # Demo data so the panel always shows meaningful state
            results["deskline"] = {
                "status": "demo",
                "rooms_total": 12,
                "rooms_occupied": 8,
                "rooms_available": 4,
                "next_checkin": "2026-06-15",
            }

        # iCal sync
        if _ICAL_URL:
            try:
                resp = await self._client.get(_ICAL_URL)
                results["ical"] = {"status": "up" if resp.status_code == 200 else "degraded", "content_length": len(resp.text)}
            except Exception as exc:
                results["ical"] = {"status": "down", "error": str(exc)}
        else:
            results["ical"] = {
                "status": "demo",
                "last_sync": "2026-06-14T10:00:00Z",
                "bookings_count": 23,
                "channels": ["Booking.com"],
            }

        # Vercel
        if _VERCEL_TOKEN:
            try:
                resp = await self._client.get(
                    "https://api.vercel.com/v6/deployments",
                    headers={"Authorization": f"Bearer {_VERCEL_TOKEN}"},
                    params={"projectId": os.environ.get("VERCEL_PROJECT_ID"), "limit": 1},
                )
                data = resp.json()
                latest = data.get("deployments", [{}])[0]
                results["vercel"] = {
                    "status": "up",
                    "latest_state": latest.get("state", "unknown"),
                    "latest_url": latest.get("url"),
                }
            except Exception as exc:
                results["vercel"] = {"status": "down", "error": str(exc)}
        else:
            results["vercel"] = {
                "status": "demo",
                "deployment_state": "READY",
                "production_url": "https://www.landhausbavaria.de",
                "last_deploy": "2026-06-13T22:30:00Z",
            }

        return results

    async def room_availability(self, date_from: str, date_to: str) -> Dict[str, Any]:
        """Fetch room availability via Deskline proxy."""
        proxy = os.environ.get("DESKLINE_PROXY_URL")
        if not proxy:
            return {"error": "DESKLINE_PROXY_URL not configured"}

        try:
            resp = await self._client.get(
                f"{proxy}/availability",
                params={"from": date_from, "to": date_to},
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.error("Deskline availability query failed: %s", exc)
            return {"error": str(exc)}

    async def website_data(self) -> Dict[str, Any]:
        """Fetch and parse public website data for Landhaus Bavaria."""
        try:
            resp = await self._client.get(_WEBSITE_URL, follow_redirects=True)
            resp.raise_for_status()
            return {"url": _WEBSITE_URL, "data": _scrape_website(resp.text, _WEBSITE_URL)}
        except Exception as exc:
            logger.error("Landhaus website data fetch failed: %s", exc)
            return {"error": str(exc)}

    async def close(self) -> None:
        await self._client.aclose()


def _scrape_website(html: str, base_url: str) -> Dict[str, Any]:
    """Extract structured public information from the Landhaus Bavaria website."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    data: Dict[str, Any] = {
        "title": _safe_text(soup.title.string) if soup.title else None,
        "description": _meta_content(soup, "description"),
        "headings": _extract_headings(soup),
        "address": _extract_address(text),
        "phone": _extract_phone(text),
        "email": _extract_email(text),
        "opening_hours": _extract_opening_hours(text),
        "weekday_specials": _extract_weekday_specials(text),
        "prices": _extract_prices(text),
        "navigation": _extract_navigation(soup, base_url),
        "images": _extract_images(soup, base_url),
        "room_keywords": _extract_room_keywords(text),
    }
    return data


def _safe_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _meta_content(soup: BeautifulSoup, name: str) -> str | None:
    meta = soup.find("meta", attrs={"name": name})
    if meta:
        return meta.get("content", "").strip() or None
    meta = soup.find("meta", attrs={"property": f"og:{name}"})
    if meta:
        return meta.get("content", "").strip() or None
    return None


def _extract_headings(soup: BeautifulSoup) -> Dict[str, List[str]]:
    return {
        "h1": [h.get_text(strip=True) for h in soup.find_all("h1")],
        "h2": [h.get_text(strip=True) for h in soup.find_all("h2")],
        "h3": [h.get_text(strip=True) for h in soup.find_all("h3")],
    }


def _extract_address(text: str) -> str | None:
    match = re.search(r"Frankfurter\s+Str\.?\s*\d+[\s\w,]*\d{5}\s+\w+", text)
    return match.group(0).strip() if match else None


def _extract_phone(text: str) -> str | None:
    match = re.search(r"0\d{3,5}\s*/\s*\d{4,10}", text)
    return match.group(0).replace(" ", "").replace("/", " / ") if match else None


def _extract_email(text: str) -> str | None:
    match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    return match.group(0) if match else None


def _extract_opening_hours(text: str) -> Dict[str, str] | None:
    # Match blocks like "Mo, Di, Mi, Sa : 11:30-14:00 & 17:30-22:00 Uhr"
    pattern = re.compile(
        r"([A-Za-z][a-z]{1,2}(?:,\s*[A-Za-z][a-z]{1,2})*)\s*[::]\s*([^\n]+?)(?=\s+(?:[A-Za-z][a-z]{1,2}(?:,\s*[A-Za-z][a-z]{1,2})*)\s*[:]|$)",
        re.IGNORECASE,
    )
    matches = pattern.findall(text)
    if not matches:
        return None
    result: Dict[str, str] = {}
    for days, hours in matches[:5]:
        for day in re.split(r",\s*", days.strip()):
            result[day.strip()] = hours.strip()
    return result


def _extract_weekday_specials(text: str) -> List[str]:
    found = []
    lower = text.lower()
    for special in _WEEKDAY_SPECIALS:
        if special.lower() in lower:
            found.append(special)
    return found


def _extract_prices(text: str) -> List[str]:
    matches = re.findall(r"\d{1,3}(?:[,.]\d{2})?\s*€", text)
    return sorted(set(matches), key=lambda x: float(x.replace("€", "").replace(",", ".").strip() or 0))


def _extract_navigation(soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
    nav: List[Dict[str, str]] = []
    seen = set()
    for link in soup.find_all("a", href=True):
        label = link.get_text(strip=True)
        href = link["href"]
        if not label or label in seen or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        if href.startswith("/"):
            href = base_url.rstrip("/") + href
        seen.add(label)
        nav.append({"label": label, "url": href})
    return nav[:12]


def _extract_images(soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
    images: List[Dict[str, str]] = []
    seen = set()
    for img in soup.find_all("img"):
        src = img.get("src")
        if not src or src in seen:
            continue
        if src.startswith("/"):
            src = base_url.rstrip("/") + src
        seen.add(src)
        images.append({"src": src, "alt": img.get("alt", "").strip()})
    return images[:10]


def _extract_room_keywords(text: str) -> List[str]:
    keywords = ["Doppelzimmer", "Einzelzimmer", "Zimmer", "Pension", "Frühstück"]
    lower = text.lower()
    return [kw for kw in keywords if kw.lower() in lower]


# Tool-adapter surface for the orchestrator
@ToolRegistry.register("landhaus_bavaria")
class LandhausBavariaTool(BaseTool):
    """Registered tool wrapper for agent integration."""

    tool_id = "landhaus_bavaria"
    is_local = True

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="landhaus_bavaria",
            description=(
                "Query Landhaus Bavaria data sources. "
                "Actions: 'health' (check all systems), "
                "'room_availability' (query Deskline for date range), "
                "'website_data' (scrape public website content)."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["health", "room_availability", "website_data"],
                        "description": "Which operation to perform.",
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD). Required for room_availability.",
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD). Required for room_availability.",
                    },
                },
                "required": ["action"],
            },
            category="domain",
            timeout_seconds=20.0,
        )

    def execute(self, action: str = "", **kwargs: Any) -> ToolResult:
        import asyncio
        import concurrent.futures

        async def _async_work():
            connector = LandhausBavariaConnector()
            try:
                if action == "health":
                    result = await connector.health()
                    return ToolResult(
                        tool_name="landhaus_bavaria",
                        content=json.dumps(result, default=str),
                        success=True,
                    )
                if action == "room_availability":
                    result = await connector.room_availability(
                        kwargs.get("date_from", ""),
                        kwargs.get("date_to", ""),
                    )
                    success = "error" not in result
                    return ToolResult(
                        tool_name="landhaus_bavaria",
                        content=json.dumps(result, default=str),
                        success=success,
                    )
                if action == "website_data":
                    result = await connector.website_data()
                    success = "error" not in result
                    return ToolResult(
                        tool_name="landhaus_bavaria",
                        content=json.dumps(result, default=str),
                        success=success,
                    )
                return ToolResult(
                    tool_name="landhaus_bavaria",
                    content=json.dumps({"error": f"Unknown action: {action}"}),
                    success=False,
                )
            finally:
                await connector.close()

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_async_work())
        # FastAPI/uvicorn already has an event loop in this thread;
        # asyncio.run() is forbidden here. Offload to a fresh thread.
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(asyncio.run, _async_work()).result(timeout=30)


__all__ = [
    "LandhausBavariaConnector",
    "LandhausBavariaTool",
]