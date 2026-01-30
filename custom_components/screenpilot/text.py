"""Text platform for ScreenPilot."""

from __future__ import annotations

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import ScreenPilotAPI, ScreenPilotError
from .const import DOMAIN
from .entity import ScreenPilotEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ScreenPilot text entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    async_add_entities(
        [
            ScreenPilotDisplayURL(coordinator, api, entry.entry_id),
            ScreenPilotStartupURL(coordinator, api, entry.entry_id),
        ]
    )


class ScreenPilotDisplayURL(ScreenPilotEntity, TextEntity):
    """Text entity for display URL."""

    _attr_translation_key = "display_url"
    _attr_icon = "mdi:web"

    def __init__(
        self,
        coordinator,
        api: ScreenPilotAPI,
        entry_id: str,
    ) -> None:
        """Initialize the text entity."""
        super().__init__(coordinator, entry_id)
        self._api = api
        self._attr_unique_id = f"{entry_id}_display_url"

    @property
    def native_value(self) -> str | None:
        """Return the current URL."""
        return self.data.current_url

    async def async_set_value(self, value: str) -> None:
        """Set the URL."""
        if not value or not value.strip():
            raise ServiceValidationError("URL cannot be empty")
        if not value.startswith(("http://", "https://", "file://")):
            raise ServiceValidationError(
                "URL must start with http://, https://, or file://"
            )
        try:
            await self._api.set_kiosk_url(value)
            await self.coordinator.async_request_refresh()
        except ScreenPilotError as err:
            raise HomeAssistantError(f"Failed to set display URL: {err}") from err


class ScreenPilotStartupURL(ScreenPilotEntity, TextEntity):
    """Text entity for startup URL."""

    _attr_translation_key = "startup_url"
    _attr_icon = "mdi:web-box"

    def __init__(
        self,
        coordinator,
        api: ScreenPilotAPI,
        entry_id: str,
    ) -> None:
        """Initialize the text entity."""
        super().__init__(coordinator, entry_id)
        self._api = api
        self._attr_unique_id = f"{entry_id}_startup_url"

    @property
    def native_value(self) -> str | None:
        """Return the startup URL."""
        return self.data.startup_url

    async def async_set_value(self, value: str) -> None:
        """Set the startup URL."""
        if not value or not value.strip():
            raise ServiceValidationError("URL cannot be empty")
        if not value.startswith(("http://", "https://", "file://")):
            raise ServiceValidationError(
                "URL must start with http://, https://, or file://"
            )
        try:
            await self._api.set_startup_url(value)
            await self.coordinator.async_request_refresh()
        except ScreenPilotError as err:
            raise HomeAssistantError(f"Failed to set startup URL: {err}") from err
