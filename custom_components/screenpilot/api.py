"""API client for ScreenPilot."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class ScreenPilotError(Exception):
    """Base exception for ScreenPilot."""


class ScreenPilotConnectionError(ScreenPilotError):
    """Connection error."""


class ScreenPilotAuthError(ScreenPilotError):
    """Authentication error."""


class ScreenPilotAPI:
    """API client for ScreenPilot."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        token: str,
        use_https: bool = False,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._host = host
        self._token = token
        self._use_https = use_https

    @property
    def base_url(self) -> str:
        """Get the base URL."""
        protocol = "https" if self._use_https else "http"
        return f"{protocol}://{self._host}"

    @property
    def _headers(self) -> dict[str, str]:
        """Get request headers."""
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an API request."""
        url = f"{self.base_url}{endpoint}"
        try:
            async with asyncio.timeout(10):
                async with self._session.request(
                    method,
                    url,
                    headers=self._headers,
                    json=json_data,
                ) as response:
                    if response.status == 401:
                        raise ScreenPilotAuthError("Invalid authentication")
                    if response.status == 404:
                        return {}
                    response.raise_for_status()
                    if response.content_type == "application/json":
                        return await response.json()
                    return {"success": True}
        except asyncio.TimeoutError as err:
            raise ScreenPilotConnectionError("Connection timeout") from err
        except aiohttp.ClientError as err:
            raise ScreenPilotConnectionError(f"Connection error: {err}") from err

    async def _get(self, endpoint: str) -> dict[str, Any]:
        """Make a GET request."""
        return await self._request("GET", endpoint)

    async def _post(
        self, endpoint: str, json_data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make a POST request."""
        return await self._request("POST", endpoint, json_data)

    async def _put(
        self, endpoint: str, json_data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make a PUT request."""
        return await self._request("PUT", endpoint, json_data)

    # Connection test
    async def test_connection(self) -> bool:
        """Test connection to ScreenPilot."""
        await self._get("/api/health/")
        return True

    # System endpoints
    async def get_system_info(self) -> dict[str, Any]:
        """Get system information."""
        return await self._get("/api/system/info/")

    async def get_display_info(self) -> dict[str, Any]:
        """Get display/monitor information."""
        return await self._get("/api/system/display/")

    async def get_health(self) -> dict[str, Any]:
        """Get comprehensive health status."""
        return await self._get("/api/health/")

    async def get_service_status(self) -> dict[str, Any]:
        """Get service status."""
        return await self._get("/api/status/service_status/")

    async def reboot_system(self) -> bool:
        """Reboot the system."""
        await self._post("/api/system/reboot/")
        return True

    async def get_reboot_schedule(self) -> dict[str, Any]:
        """Get the scheduled-reboot configuration."""
        return await self._get("/api/system/reboot-schedule/")

    # Kiosk endpoints
    async def get_kiosk_url(self) -> dict[str, Any]:
        """Get current kiosk URL."""
        return await self._get("/api/kiosk/url/")

    async def set_kiosk_url(self, url: str) -> bool:
        """Set the kiosk URL."""
        await self._put("/api/kiosk/url/", {"url": url})
        return True

    async def get_startup_url(self) -> dict[str, Any]:
        """Get startup URL."""
        return await self._get("/api/kiosk/startup_url/")

    async def set_startup_url(self, url: str) -> bool:
        """Set the startup URL."""
        await self._put("/api/kiosk/startup_url/", {"url": url})
        return True

    async def get_kiosk_health(self) -> dict[str, Any]:
        """Get kiosk browser health."""
        return await self._get("/api/kiosk/health/")

    async def reload_page(self) -> bool:
        """Reload the current page."""
        await self._get("/api/kiosk/reload_currenturl/")
        return True

    async def hard_refresh(self) -> bool:
        """Hard refresh with cache clearing."""
        await self._post("/api/kiosk/hard-refresh/")
        return True

    async def restart_browser(self) -> bool:
        """Restart the browser service."""
        await self._get("/api/kiosk/reload/")
        return True

    async def clear_data(self, data_type: str = "all") -> bool:
        """Clear browser data."""
        await self._post("/api/kiosk/clear_data/", {"type": data_type})
        return True

    async def get_zoom(self) -> dict[str, Any]:
        """Get zoom level."""
        return await self._get("/api/kiosk/zoom/")

    async def set_zoom(self, level: int) -> bool:
        """Set zoom level (25-500)."""
        await self._post("/api/kiosk/zoom/", {"zoom": level})
        return True

    async def set_session_mode(self, mode: str) -> bool:
        """Set session mode."""
        await self._post("/api/kiosk/session_mode/", {"mode": mode})
        return True

    async def execute_javascript(self, script: str) -> dict[str, Any]:
        """Execute JavaScript in browser."""
        return await self._post(
            "/api/kiosk/devtools/execute/", {"expression": script}
        )

    async def get_devtools_version(self) -> dict[str, Any]:
        """Get Chrome DevTools version info."""
        return await self._get("/api/kiosk/devtools/version/")

    # CEC endpoints
    async def get_cec_status(self) -> dict[str, Any]:
        """Get CEC status."""
        return await self._get("/api/cec/status/")

    async def get_cec_detection_status(self) -> dict[str, Any]:
        """Get CEC capability-detection status."""
        return await self._get("/api/cec/detection-status/")

    async def refresh_cec_capabilities(self) -> bool:
        """Trigger CEC capability detection."""
        await self._post("/api/cec/refresh_capabilities/")
        return True

    async def get_cec_command_history(self, limit: int = 5) -> dict[str, Any]:
        """Get recent CEC command-history entries (most recent first)."""
        return await self._get(f"/api/cec/command-history/?limit={limit}")

    async def send_cec_command(self, command: str) -> bool:
        """Send a CEC command."""
        await self._post(f"/api/cec/command/{command}/")
        return True

    # Screenshot
    def get_screenshot_url(self) -> str:
        """Get the screenshot URL."""
        return f"{self.base_url}/api/kiosk/screenshot/"

    async def get_screenshot(self) -> bytes | None:
        """Get screenshot bytes."""
        url = self.get_screenshot_url()
        try:
            async with asyncio.timeout(10):
                async with self._session.get(url, headers=self._headers) as response:
                    response.raise_for_status()
                    return await response.read()
        except Exception as err:
            _LOGGER.error("Failed to get screenshot: %s", err)
            return None
