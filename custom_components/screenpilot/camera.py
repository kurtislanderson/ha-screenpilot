"""Camera platform for ScreenPilot."""
from __future__ import annotations

import logging

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import ScreenPilotAPI
from .const import DOMAIN
from .entity import ScreenPilotEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ScreenPilot camera."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    async_add_entities([ScreenPilotCamera(coordinator, api, entry.entry_id)])


class ScreenPilotCamera(ScreenPilotEntity, Camera):
    """Camera for ScreenPilot screenshots."""

    _attr_translation_key = "screenshot"

    def __init__(
        self,
        coordinator,
        api: ScreenPilotAPI,
        entry_id: str,
    ) -> None:
        """Initialize the camera."""
        super().__init__(coordinator, entry_id)
        self._api = api
        self._attr_unique_id = f"{entry_id}_screenshot"
        # Set frame interval (normally done by Camera.__init__)
        self._attr_frame_interval = 0.5

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a still image from the camera."""
        return await self._api.get_screenshot()
