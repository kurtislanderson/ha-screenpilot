"""Switch platform for ScreenPilot integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, ICON_TV

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ScreenPilot switch platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    api = data["api"]
    coordinator = data["coordinators"]["cec"]
    name = data["name"]
    
    async_add_entities([
        ScreenPilotTVSwitch(
            coordinator,
            api,
            name,
            config_entry.entry_id,
        )
    ])


class ScreenPilotTVSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a ScreenPilot TV power switch."""
    
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        api,
        name: str,
        entry_id: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{entry_id}_tv_power"
        self._attr_name = f"{name} TV"
        self._attr_icon = ICON_TV
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=name,
            manufacturer="ScreenPilot",
            model="Kiosk Display",
        )
        
    @property
    def is_on(self) -> bool:
        """Return true if the TV is on."""
        if self.coordinator.data is None:
            return False
        return self.coordinator.data.get("power_status", "unknown") == "on"
        
    @property
    def available(self) -> bool:
        """Return true if the TV is available."""
        if self.coordinator.data is None:
            return False
        return self.coordinator.data.get("tv_present", False)
        
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the TV on."""
        await self._api.send_cec_command("power_on")
        await self.coordinator.async_request_refresh()
        
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the TV off."""
        await self._api.send_cec_command("power_off")
        await self.coordinator.async_request_refresh()