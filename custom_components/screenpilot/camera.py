"""Camera platform for ScreenPilot integration."""
from __future__ import annotations

import logging

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ScreenPilot camera platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    api = data["api"]
    name = data["name"]
    
    async_add_entities([
        ScreenPilotCamera(
            api,
            name,
            config_entry.entry_id,
        )
    ])


class ScreenPilotCamera(Camera):
    """Representation of a ScreenPilot screenshot camera."""
    
    def __init__(
        self,
        api,
        name: str,
        entry_id: str,
    ) -> None:
        """Initialize the camera."""
        super().__init__()
        self._api = api
        self._attr_unique_id = f"{entry_id}_screenshot"
        self._attr_name = f"{name} Display"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=name,
            manufacturer="ScreenPilot",
            model="Kiosk Display",
        )
        
    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a still image from the camera."""
        try:
            url = self._api.get_screenshot_url()
            response = await self._api._session.get(url)
            response.raise_for_status()
            return await response.read()
        except Exception as err:
            _LOGGER.error("Failed to get screenshot: %s", err)
            return None