"""Text platform for ScreenPilot integration."""
from __future__ import annotations

import logging

from homeassistant.components.text import TextEntity, TextEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, ICON_URL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ScreenPilot text platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    api = data["api"]
    coordinator = data["coordinators"]["kiosk"]
    name = data["name"]
    
    async_add_entities([
        ScreenPilotURLText(
            coordinator,
            api,
            name,
            config_entry.entry_id,
        )
    ])


class ScreenPilotURLText(CoordinatorEntity, TextEntity):
    """Representation of a ScreenPilot URL text input."""
    
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        api,
        name: str,
        entry_id: str,
    ) -> None:
        """Initialize the text entity."""
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{entry_id}_url"
        self._attr_name = f"{name} URL"
        self._attr_icon = ICON_URL
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=name,
            manufacturer="ScreenPilot",
            model="Kiosk Display",
        )
        
    @property
    def native_value(self) -> str | None:
        """Return the current URL."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("url", "")
        
    async def async_set_value(self, value: str) -> None:
        """Set the URL."""
        await self._api.set_kiosk_url(value)
        await self.coordinator.async_request_refresh()