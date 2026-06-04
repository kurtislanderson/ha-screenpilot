"""Sensor platform for ScreenPilot."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ScreenPilotData
from .entity import ScreenPilotEntity


@dataclass(frozen=True, kw_only=True)
class ScreenPilotSensorDescription(SensorEntityDescription):
    """Describes a ScreenPilot sensor."""

    value_fn: Callable[[ScreenPilotData], Any]
    attr_fn: Callable[[ScreenPilotData], dict[str, Any]] | None = None


def format_uptime(seconds: int) -> str:
    """Format uptime to human readable string."""
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


SENSORS: tuple[ScreenPilotSensorDescription, ...] = (
    # System sensors
    ScreenPilotSensorDescription(
        key="cpu_percent",
        translation_key="cpu_percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cpu-64-bit",
        value_fn=lambda data: round(data.cpu_percent, 1),
    ),
    ScreenPilotSensorDescription(
        key="memory_percent",
        translation_key="memory_percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:memory",
        value_fn=lambda data: round(data.memory_percent, 1),
    ),
    ScreenPilotSensorDescription(
        key="disk_percent",
        translation_key="disk_percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:harddisk",
        value_fn=lambda data: round(data.disk_percent, 1),
    ),
    ScreenPilotSensorDescription(
        key="uptime",
        translation_key="uptime",
        icon="mdi:timer-outline",
        value_fn=lambda data: format_uptime(data.uptime),
    ),
    ScreenPilotSensorDescription(
        key="ip_address",
        translation_key="ip_address",
        icon="mdi:ip-network",
        value_fn=lambda data: data.ip_address,
    ),
    # Kiosk sensors
    ScreenPilotSensorDescription(
        key="current_url",
        translation_key="current_url",
        icon="mdi:web",
        value_fn=lambda data: data.current_url[:255] if data.current_url else "",
    ),
    ScreenPilotSensorDescription(
        key="startup_url",
        translation_key="startup_url",
        icon="mdi:web-box",
        value_fn=lambda data: data.startup_url[:255] if data.startup_url else "",
    ),
    ScreenPilotSensorDescription(
        key="zoom_level",
        translation_key="zoom_level",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:magnify",
        value_fn=lambda data: data.zoom_level,
    ),
    ScreenPilotSensorDescription(
        key="session_mode",
        translation_key="session_mode",
        icon="mdi:lock",
        value_fn=lambda data: data.session_mode,
    ),
    # Health sensors
    ScreenPilotSensorDescription(
        key="health_status",
        translation_key="health_status",
        icon="mdi:heart-pulse",
        value_fn=lambda data: data.health_status,
    ),
    ScreenPilotSensorDescription(
        key="heartbeat_age",
        translation_key="heartbeat_age",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heart-flash",
        value_fn=lambda data: data.heartbeat_age,
    ),
    ScreenPilotSensorDescription(
        key="chrome_version",
        translation_key="chrome_version",
        icon="mdi:google-chrome",
        value_fn=lambda data: data.chrome_version,
    ),
    ScreenPilotSensorDescription(
        key="last_heartbeat",
        translation_key="last_heartbeat",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:heart-flash",
        value_fn=lambda data: data.last_heartbeat,
    ),
    # Network sensors
    ScreenPilotSensorDescription(
        key="services_active",
        translation_key="services_active",
        icon="mdi:cog-sync",
        value_fn=lambda data: f"{data.services_active}/{data.services_total}",
        attr_fn=lambda data: {
            "active": data.services_active,
            "total": data.services_total,
            "failed": data.services_failed,
            "failed_services": data.failed_services,
        },
    ),
    # Display sensors
    ScreenPilotSensorDescription(
        key="display_resolution",
        translation_key="display_resolution",
        icon="mdi:monitor-screenshot",
        value_fn=lambda data: data.display_resolution,
        attr_fn=lambda data: {"refresh_rate": data.display_refresh_rate},
    ),
    # CEC sensors
    ScreenPilotSensorDescription(
        key="tv_power_status",
        translation_key="tv_power_status",
        icon="mdi:television",
        value_fn=lambda data: (
            "on" if data.tv_power_on else "off" if data.tv_present else "unavailable"
        ),
    ),
    ScreenPilotSensorDescription(
        key="cec_detection_status",
        translation_key="cec_detection_status",
        icon="mdi:magnify-scan",
        value_fn=lambda data: data.cec_detection_status,
        attr_fn=lambda data: {"progress": data.cec_detection_progress},
    ),
    ScreenPilotSensorDescription(
        key="last_cec_command",
        translation_key="last_cec_command",
        icon="mdi:remote-tv",
        value_fn=lambda data: data.last_cec_command or "none",
        attr_fn=lambda data: {
            "success": data.last_cec_command_success,
            "executed_at": data.last_cec_command_at,
            "count": data.cec_command_count,
        },
    ),
    # System sensors
    ScreenPilotSensorDescription(
        key="reboot_schedule",
        translation_key="reboot_schedule",
        icon="mdi:calendar-clock",
        value_fn=lambda data: (
            f"{data.reboot_frequency} {data.reboot_time}".strip()
            if data.reboot_enabled
            else "disabled"
        ),
        attr_fn=lambda data: {
            "enabled": data.reboot_enabled,
            "frequency": data.reboot_frequency,
            "time": data.reboot_time,
            "next_reboot": data.reboot_next,
            "cron": data.reboot_cron,
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ScreenPilot sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities(
        ScreenPilotSensor(coordinator, entry.entry_id, description)
        for description in SENSORS
    )


class ScreenPilotSensor(ScreenPilotEntity, SensorEntity):
    """Sensor for ScreenPilot."""

    entity_description: ScreenPilotSensorDescription

    def __init__(
        self,
        coordinator,
        entry_id: str,
        description: ScreenPilotSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry_id)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if self.entity_description.attr_fn is None:
            return None
        return self.entity_description.attr_fn(self.data)
