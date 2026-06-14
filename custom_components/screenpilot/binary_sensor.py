"""Binary sensor platform for ScreenPilot."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ScreenPilotData
from .entity import ScreenPilotEntity


@dataclass(frozen=True, kw_only=True)
class ScreenPilotBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a ScreenPilot binary sensor."""

    value_fn: Callable[[ScreenPilotData], bool | None]


BINARY_SENSORS: tuple[ScreenPilotBinarySensorDescription, ...] = (
    # Health sensors
    ScreenPilotBinarySensorDescription(
        key="system_healthy",
        translation_key="system_healthy",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: not data.system_healthy,
    ),
    ScreenPilotBinarySensorDescription(
        key="browser_connected",
        translation_key="browser_connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda data: data.browser_connected,
    ),
    ScreenPilotBinarySensorDescription(
        key="browser_healthy",
        translation_key="browser_healthy",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: not data.browser_healthy,
    ),
    # Service sensors
    ScreenPilotBinarySensorDescription(
        key="services_healthy",
        translation_key="services_healthy",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: not data.services_healthy,
    ),
    ScreenPilotBinarySensorDescription(
        key="kiosk_service",
        translation_key="kiosk_service",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda data: data.kiosk_service_running,
    ),
    ScreenPilotBinarySensorDescription(
        key="webconsole_service",
        translation_key="webconsole_service",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda data: data.webconsole_service_running,
    ),
    ScreenPilotBinarySensorDescription(
        key="cec_service",
        translation_key="cec_service",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda data: data.cec_service_running,
    ),
    # Network sensors
    ScreenPilotBinarySensorDescription(
        key="network_connected",
        translation_key="network_connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda data: data.ethernet_connected or data.wifi_connected,
    ),
    # Navigation overlay
    ScreenPilotBinarySensorDescription(
        key="overlay_visible",
        translation_key="overlay_visible",
        value_fn=lambda data: data.overlay_visible,
    ),
    # CEC sensors
    ScreenPilotBinarySensorDescription(
        key="tv_present",
        translation_key="tv_present",
        device_class=BinarySensorDeviceClass.PRESENCE,
        value_fn=lambda data: data.tv_present,
    ),
    ScreenPilotBinarySensorDescription(
        key="tv_power",
        translation_key="tv_power",
        device_class=BinarySensorDeviceClass.POWER,
        value_fn=lambda data: data.tv_power_on,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ScreenPilot binary sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities(
        ScreenPilotBinarySensor(coordinator, entry.entry_id, description)
        for description in BINARY_SENSORS
    )


class ScreenPilotBinarySensor(ScreenPilotEntity, BinarySensorEntity):
    """Binary sensor for ScreenPilot."""

    entity_description: ScreenPilotBinarySensorDescription

    def __init__(
        self,
        coordinator,
        entry_id: str,
        description: ScreenPilotBinarySensorDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry_id)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self.entity_description.value_fn(self.data)
