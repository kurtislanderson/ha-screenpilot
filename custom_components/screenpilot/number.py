"""Number platform for ScreenPilot."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import ScreenPilotAPI, ScreenPilotError
from .const import DOMAIN
from .entity import ScreenPilotEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ScreenPilot number entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    async_add_entities(
        [
            # Kiosk numbers
            ScreenPilotZoom(coordinator, api, entry.entry_id),
        ]
    )


class ScreenPilotZoom(ScreenPilotEntity, NumberEntity):
    """Number entity for zoom level."""

    _attr_translation_key = "zoom_level"
    _attr_icon = "mdi:magnify-plus-outline"
    _attr_native_min_value = 25
    _attr_native_max_value = 500
    _attr_native_step = 5
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator,
        api: ScreenPilotAPI,
        entry_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, entry_id)
        self._api = api
        self._attr_unique_id = f"{entry_id}_zoom"

    @property
    def native_value(self) -> float:
        """Return the current zoom level."""
        return self.data.zoom_level

    async def async_set_native_value(self, value: float) -> None:
        """Set the zoom level."""
        try:
            await self._api.set_zoom(int(value))
            await self.coordinator.async_request_refresh()
        except ScreenPilotError as err:
            raise HomeAssistantError(f"Failed to set zoom level: {err}") from err
