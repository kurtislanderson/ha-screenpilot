"""Switch platform for ScreenPilot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import ScreenPilotError
from .const import DOMAIN
from .entity import ScreenPilotEntity


@dataclass(frozen=True, kw_only=True)
class ScreenPilotSwitchDescription(SwitchEntityDescription):
    """Describes a ScreenPilot switch."""

    on_command: str
    off_command: str


SWITCHES: tuple[ScreenPilotSwitchDescription, ...] = (
    ScreenPilotSwitchDescription(
        key="tv_power",
        translation_key="tv_power",
        icon="mdi:television",
        on_command="power_on",
        off_command="power_off",
    ),
    ScreenPilotSwitchDescription(
        key="screen_power",
        translation_key="screen_power",
        icon="mdi:monitor",
        on_command="active_source",
        off_command="inactive_source",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ScreenPilot switches."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    async_add_entities(
        ScreenPilotSwitch(coordinator, api, entry.entry_id, description)
        for description in SWITCHES
    )


class ScreenPilotSwitch(ScreenPilotEntity, SwitchEntity):
    """Switch for ScreenPilot."""

    entity_description: ScreenPilotSwitchDescription

    def __init__(
        self,
        coordinator,
        api,
        entry_id: str,
        description: ScreenPilotSwitchDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, entry_id)
        self._api = api
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        if self.entity_description.key == "tv_power":
            return self.data.tv_power_on
        # For screen power, we don't have a direct state, assume on if TV is on
        return self.data.tv_power_on

    @property
    def available(self) -> bool:
        """Return true if the switch is available."""
        return super().available and self.data.tv_present

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        try:
            await self._api.send_cec_command(self.entity_description.on_command)
            await self.coordinator.async_request_refresh()
        except ScreenPilotError as err:
            raise HomeAssistantError(f"Failed to turn on {self.name}: {err}") from err

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        try:
            await self._api.send_cec_command(self.entity_description.off_command)
            await self.coordinator.async_request_refresh()
        except ScreenPilotError as err:
            raise HomeAssistantError(f"Failed to turn off {self.name}: {err}") from err
