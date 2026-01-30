"""DataUpdateCoordinator for ScreenPilot."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ScreenPilotAPI, ScreenPilotConnectionError, ScreenPilotAuthError
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


@dataclass
class ScreenPilotData:
    """Data from ScreenPilot device."""

    # System
    hostname: str = ""
    ip_address: str = ""
    uptime: int = 0
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0

    # Health
    system_healthy: bool = False
    health_status: str = "unknown"
    browser_connected: bool = False
    browser_healthy: bool = False
    heartbeat_age: int = 999
    chrome_version: str = ""

    # Services
    services_healthy: bool = False
    kiosk_service_running: bool = False
    webconsole_service_running: bool = False
    cec_service_running: bool = False

    # Kiosk
    current_url: str = ""
    startup_url: str = ""
    zoom_level: int = 100
    session_mode: str = "persistent"

    # CEC
    tv_present: bool = False
    tv_power_on: bool = False
    available_commands: list[str] | None = None

    def __post_init__(self) -> None:
        """Initialize mutable defaults."""
        if self.available_commands is None:
            self.available_commands = []


class ScreenPilotCoordinator(DataUpdateCoordinator[ScreenPilotData]):
    """Coordinator for ScreenPilot data updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: ScreenPilotAPI,
        name: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.api = api
        self.device_name = name

    async def _async_update_data(self) -> ScreenPilotData:
        """Fetch data from ScreenPilot."""
        try:
            # Fetch all data in parallel
            results = await asyncio.gather(
                self.api.get_health(),
                self.api.get_system_info(),
                self.api.get_kiosk_url(),
                self.api.get_kiosk_health(),
                self.api.get_startup_url(),
                self.api.get_zoom(),
                self.api.get_cec_status(),
                self.api.get_service_status(),
                return_exceptions=True,
            )

            health, system, kiosk_url, kiosk_health, startup, zoom, cec, services = results

            # Handle exceptions gracefully
            def safe_get(data: Any, default: Any = None) -> Any:
                if isinstance(data, Exception):
                    return default if default is not None else {}
                return data

            health = safe_get(health, {})
            system = safe_get(system, {})
            kiosk_url = safe_get(kiosk_url, {})
            kiosk_health = safe_get(kiosk_health, {})
            startup = safe_get(startup, {})
            zoom = safe_get(zoom, {})
            cec = safe_get(cec, {})
            services = safe_get(services, {})

            # Parse system info
            memory = system.get("memory", {})
            disk = system.get("disk", {})

            # Parse services
            services_list = services.get("services", [])
            service_states = {
                s.get("name", ""): s.get("status") == "active"
                for s in services_list
                if isinstance(s, dict)
            }

            # Build data object
            return ScreenPilotData(
                # System
                hostname=system.get("hostname", ""),
                ip_address=system.get("ip_address", ""),
                uptime=system.get("uptime", 0),
                cpu_percent=system.get("cpu_percent", 0.0),
                memory_percent=memory.get("percent", 0.0) if isinstance(memory, dict) else 0.0,
                disk_percent=disk.get("percent", 0.0) if isinstance(disk, dict) else 0.0,
                # Health
                system_healthy=health.get("status") == "healthy",
                health_status=health.get("status", "unknown"),
                browser_connected=kiosk_health.get("browser_connected", False),
                browser_healthy=kiosk_health.get("heartbeat_age", 999) < 120,
                heartbeat_age=kiosk_health.get("heartbeat_age", 999),
                chrome_version=kiosk_health.get("chrome_version", ""),
                # Services
                services_healthy=services.get("all_healthy", False),
                kiosk_service_running=service_states.get("screenpilot-kiosk.service", False),
                webconsole_service_running=service_states.get("screenpilot-webconsole.service", False),
                cec_service_running=service_states.get("screenpilot-cec-daemon.service", False),
                # Kiosk
                current_url=kiosk_url.get("url", ""),
                startup_url=startup.get("url", ""),
                zoom_level=zoom.get("zoom", 100),
                session_mode=kiosk_health.get("session_mode", "persistent"),
                # CEC
                tv_present=cec.get("tv_present", False),
                tv_power_on=cec.get("power_status") == "on",
                available_commands=cec.get("available_commands", []),
            )

        except ScreenPilotAuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except ScreenPilotConnectionError as err:
            raise UpdateFailed(f"Connection failed: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err
