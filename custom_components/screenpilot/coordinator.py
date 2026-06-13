"""DataUpdateCoordinator for ScreenPilot."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ScreenPilotAPI, ScreenPilotConnectionError, ScreenPilotAuthError
from .const import UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


def _parse_dt(value: Any) -> datetime | None:
    """Parse an ISO timestamp into an aware datetime (None if unparseable)."""
    if not isinstance(value, str) or not value:
        return None
    try:
        ts = datetime.fromisoformat(value)
    except ValueError:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts


def _heartbeat_age(last_heartbeat: Any) -> int:
    """Return seconds since the browser's last heartbeat (999 if unknown)."""
    ts = _parse_dt(last_heartbeat)
    if ts is None:
        return 999
    return int((datetime.now(timezone.utc) - ts).total_seconds())


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

    last_heartbeat: datetime | None = None

    # Network
    ethernet_connected: bool = False
    wifi_connected: bool = False

    # Services
    services_healthy: bool = False
    kiosk_service_running: bool = False
    webconsole_service_running: bool = False
    cec_service_running: bool = False
    services_total: int = 0
    services_active: int = 0
    services_failed: int = 0
    failed_services: list[str] | None = None

    # Kiosk
    current_url: str = ""
    startup_url: str = ""
    zoom_level: int = 100
    session_mode: str = "persistent"

    # Display
    display_resolution: str = ""
    display_refresh_rate: float = 0.0

    # Reboot schedule
    reboot_enabled: bool = False
    reboot_frequency: str = ""
    reboot_time: str = ""
    reboot_next: str = ""
    reboot_cron: str = ""

    # CEC
    tv_present: bool = False
    tv_power_on: bool = False
    available_commands: list[str] | None = None
    cec_detection_status: str = "unknown"
    cec_detection_progress: int = 0
    last_cec_command: str = ""
    last_cec_command_success: bool = False
    last_cec_command_at: str = ""
    cec_command_count: int = 0

    def __post_init__(self) -> None:
        """Initialize mutable defaults."""
        if self.available_commands is None:
            self.available_commands = []
        if self.failed_services is None:
            self.failed_services = []


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
            labels = (
                "health",
                "system",
                "kiosk_url",
                "kiosk_health",
                "startup",
                "zoom",
                "cec",
                "services",
                "cec_detection",
                "display",
                "reboot_schedule",
                "cec_history",
            )
            results = await asyncio.gather(
                self.api.get_health(),
                self.api.get_system_info(),
                self.api.get_kiosk_url(),
                self.api.get_kiosk_health(),
                self.api.get_startup_url(),
                self.api.get_zoom(),
                self.api.get_cec_status(),
                self.api.get_service_status(),
                self.api.get_cec_detection_status(),
                self.api.get_display_info(),
                self.api.get_reboot_schedule(),
                self.api.get_cec_command_history(),
                return_exceptions=True,
            )

            # Log which individual calls failed so schema/endpoint drift is
            # visible instead of silently collapsing to default values.
            for label, res in zip(labels, results):
                if isinstance(res, Exception):
                    _LOGGER.debug("ScreenPilot '%s' fetch failed: %s", label, res)

            (
                health,
                system,
                kiosk_url,
                kiosk_health,
                startup,
                zoom,
                cec,
                services,
                cec_detection,
                display,
                reboot,
                cec_history,
            ) = results

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
            cec_detection = safe_get(cec_detection, {})
            display = safe_get(display, {})
            reboot = safe_get(reboot, {})
            cec_history = safe_get(cec_history, {})

            # Parse system info
            memory = system.get("memory", {})
            disk = system.get("disk", {})

            # Parse network + systemd aggregate from the unified health payload.
            checks = health.get("checks", {}) if isinstance(health, dict) else {}
            network = checks.get("network", {}) if isinstance(checks, dict) else {}
            ethernet = network.get("ethernet", {}) if isinstance(network, dict) else {}
            wifi = network.get("wifi", {}) if isinstance(network, dict) else {}
            systemd = (
                checks.get("systemd_services", {}) if isinstance(checks, dict) else {}
            )
            systemd_units = (
                systemd.get("services", {}) if isinstance(systemd, dict) else {}
            )
            failed_services = [
                name
                for name, info in systemd_units.items()
                if isinstance(info, dict) and info.get("state") == "failed"
            ]

            # Parse display
            display_current = (
                display.get("current", {}) if isinstance(display, dict) else {}
            )

            # Parse reboot schedule
            schedule = reboot.get("schedule", {}) if isinstance(reboot, dict) else {}

            # Parse CEC command history (most recent entry first)
            cec_logs = (
                cec_history.get("logs", []) if isinstance(cec_history, dict) else []
            )
            last_cec = cec_logs[0] if cec_logs and isinstance(cec_logs[0], dict) else {}

            # Parse services. The /api/status/service_status/ endpoint returns a
            # flat dict keyed by service name: {"<svc>.service": {"active_state":
            # "active"|"inactive"|"failed", ...}, ...}.
            service_states = {
                name: info.get("active_state") == "active"
                for name, info in services.items()
                if isinstance(info, dict)
            }
            # Healthy unless any unit is in a failed state. Oneshot units that go
            # inactive after completing (e.g. cleanup) are not treated as failures.
            services_healthy = isinstance(services, dict) and not any(
                isinstance(info, dict) and info.get("active_state") == "failed"
                for info in services.values()
            )

            # Build data object
            return ScreenPilotData(
                # System
                hostname=system.get("hostname", ""),
                ip_address=system.get("ip_address", ""),
                uptime=system.get("uptime", 0),
                cpu_percent=system.get("cpu_percent", 0.0),
                memory_percent=memory.get("percent", 0.0)
                if isinstance(memory, dict)
                else 0.0,
                disk_percent=disk.get("percent", 0.0)
                if isinstance(disk, dict)
                else 0.0,
                # Health
                system_healthy=health.get("status") == "healthy",
                health_status=health.get("status", "unknown"),
                browser_connected=kiosk_health.get("healthy", False),
                browser_healthy=kiosk_health.get("healthy", False),
                heartbeat_age=_heartbeat_age(kiosk_health.get("last_heartbeat")),
                chrome_version=kiosk_health.get("browser_version", ""),
                last_heartbeat=_parse_dt(kiosk_health.get("last_heartbeat")),
                # Network
                ethernet_connected=bool(ethernet.get("connected")),
                wifi_connected=bool(wifi.get("connected")),
                # Services
                services_healthy=services_healthy,
                # Display-stack-aware: a Wayland deploy runs screenpilot-kiosk-wayland
                # while the legacy screenpilot-kiosk is intentionally dormant (and vice
                # versa on X11). Report the kiosk as running if EITHER unit is active so
                # the sensor doesn't silently read False on a healthy Wayland kiosk.
                kiosk_service_running=bool(
                    service_states.get("screenpilot-kiosk-wayland.service")
                    or service_states.get("screenpilot-kiosk.service")
                ),
                webconsole_service_running=service_states.get(
                    "screenpilot-webconsole.service", False
                ),
                # The CEC detector is an on-demand oneshot (fires via
                # refresh_cec_capabilities then exits), so it is normally
                # inactive. The persistent daemon that owns HDMI/CEC monitoring
                # is hdmi-monitor; use it as the "service running" signal.
                cec_service_running=service_states.get(
                    "screenpilot-hdmi-monitor.service", False
                ),
                services_total=systemd.get("total", 0),
                services_active=systemd.get("active", 0),
                services_failed=systemd.get("failed", 0),
                failed_services=failed_services,
                # Kiosk
                current_url=kiosk_url.get("url", ""),
                startup_url=startup.get("url", ""),
                zoom_level=zoom.get("zoom", 100),
                session_mode=kiosk_health.get("session_mode", "persistent"),
                # Display
                display_resolution=display_current.get("resolution", ""),
                display_refresh_rate=display_current.get("refresh_rate", 0.0),
                # Reboot schedule
                reboot_enabled=bool(schedule.get("enabled")),
                reboot_frequency=schedule.get("frequency", ""),
                reboot_time=schedule.get("time", ""),
                reboot_next=schedule.get("next_reboot") or "",
                reboot_cron=reboot.get("cron_expression", ""),
                # CEC
                tv_present=cec.get("tv_present", False),
                tv_power_on=cec.get("power_status") == "on",
                available_commands=cec.get("available_commands", []),
                cec_detection_status=cec_detection.get("status", "unknown"),
                cec_detection_progress=cec_detection.get("progress", 0),
                last_cec_command=last_cec.get("command_key", ""),
                last_cec_command_success=bool(last_cec.get("success")),
                last_cec_command_at=last_cec.get("executed_at") or "",
                cec_command_count=cec_history.get("count", 0),
            )

        except ScreenPilotAuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except ScreenPilotConnectionError as err:
            raise UpdateFailed(f"Connection failed: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err
