"""Select platform for ScreenPilot."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import ScreenPilotAPI, ScreenPilotError
from .const import DOMAIN, HDMI_INPUTS, SESSION_MODES
from .entity import ScreenPilotEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ScreenPilot select entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    async_add_entities(
        [
            # Kiosk selects
            ScreenPilotSessionMode(coordinator, api, entry.entry_id),
            # CEC selects
            ScreenPilotHDMIInput(coordinator, api, entry.entry_id),
        ]
    )


class ScreenPilotHDMIInput(ScreenPilotEntity, SelectEntity):
    """Select entity for HDMI input."""

    _attr_translation_key = "hdmi_input"
    _attr_icon = "mdi:video-input-hdmi"
    _attr_options = list(HDMI_INPUTS.keys())

    def __init__(
        self,
        coordinator,
        api: ScreenPilotAPI,
        entry_id: str,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator, entry_id)
        self._api = api
        self._attr_unique_id = f"{entry_id}_hdmi_input"
        self._current_option: str | None = None

    @property
    def current_option(self) -> str | None:
        """Return the current option."""
        return self._current_option

    @property
    def available(self) -> bool:
        """Return true if the select is available."""
        return super().available and self.data.tv_present

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        command = HDMI_INPUTS.get(option)
        if command:
            try:
                await self._api.send_cec_command(command)
                self._current_option = option
                await self.coordinator.async_request_refresh()
            except ScreenPilotError as err:
                raise HomeAssistantError(f"Failed to select HDMI input: {err}") from err


class ScreenPilotSessionMode(ScreenPilotEntity, SelectEntity):
    """Select entity for session mode."""

    _attr_translation_key = "session_mode"
    _attr_icon = "mdi:lock"
    _attr_options = SESSION_MODES

    def __init__(
        self,
        coordinator,
        api: ScreenPilotAPI,
        entry_id: str,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator, entry_id)
        self._api = api
        self._attr_unique_id = f"{entry_id}_session_mode"

    @property
    def current_option(self) -> str | None:
        """Return the current session mode."""
        return self.data.session_mode

    async def async_select_option(self, option: str) -> None:
        """Change the session mode."""
        try:
            await self._api.set_session_mode(option)
            await self.coordinator.async_request_refresh()
        except ScreenPilotError as err:
            raise HomeAssistantError(f"Failed to set session mode: {err}") from err
