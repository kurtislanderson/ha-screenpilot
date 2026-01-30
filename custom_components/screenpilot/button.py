"""Button platform for ScreenPilot."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import ScreenPilotAPI, ScreenPilotError
from .const import DOMAIN
from .entity import ScreenPilotEntity


@dataclass(frozen=True, kw_only=True)
class ScreenPilotButtonDescription(ButtonEntityDescription):
    """Describes a ScreenPilot button."""

    press_fn: Callable[[ScreenPilotAPI], Awaitable[bool]]
    refresh_after: bool = True


BUTTONS: tuple[ScreenPilotButtonDescription, ...] = (
    ScreenPilotButtonDescription(
        key="reload_page",
        translation_key="reload_page",
        icon="mdi:refresh",
        press_fn=lambda api: api.reload_page(),
    ),
    ScreenPilotButtonDescription(
        key="hard_refresh",
        translation_key="hard_refresh",
        icon="mdi:refresh-circle",
        press_fn=lambda api: api.hard_refresh(),
    ),
    ScreenPilotButtonDescription(
        key="load_start_url",
        translation_key="load_start_url",
        icon="mdi:home",
        press_fn=lambda api: api.reload_page(),  # Will navigate to startup URL
    ),
    ScreenPilotButtonDescription(
        key="restart_browser",
        translation_key="restart_browser",
        icon="mdi:restart",
        press_fn=lambda api: api.restart_browser(),
    ),
    ScreenPilotButtonDescription(
        key="clear_cache",
        translation_key="clear_cache",
        icon="mdi:delete-sweep",
        press_fn=lambda api: api.clear_data("cache"),
        refresh_after=False,
    ),
    ScreenPilotButtonDescription(
        key="clear_all_data",
        translation_key="clear_all_data",
        icon="mdi:delete-forever",
        press_fn=lambda api: api.clear_data("all"),
        refresh_after=False,
    ),
    ScreenPilotButtonDescription(
        key="reboot_device",
        translation_key="reboot_device",
        icon="mdi:restart-alert",
        press_fn=lambda api: api.reboot_system(),
        refresh_after=False,
    ),
    ScreenPilotButtonDescription(
        key="volume_up",
        translation_key="volume_up",
        icon="mdi:volume-plus",
        press_fn=lambda api: api.send_cec_command("volume_up"),
        refresh_after=False,
    ),
    ScreenPilotButtonDescription(
        key="volume_down",
        translation_key="volume_down",
        icon="mdi:volume-minus",
        press_fn=lambda api: api.send_cec_command("volume_down"),
        refresh_after=False,
    ),
    ScreenPilotButtonDescription(
        key="mute_toggle",
        translation_key="mute_toggle",
        icon="mdi:volume-mute",
        press_fn=lambda api: api.send_cec_command("mute_toggle"),
        refresh_after=False,
    ),
    ScreenPilotButtonDescription(
        key="power_toggle",
        translation_key="power_toggle",
        icon="mdi:power",
        press_fn=lambda api: api.send_cec_command("power_toggle"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ScreenPilot buttons."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    async_add_entities(
        ScreenPilotButton(coordinator, api, entry.entry_id, description)
        for description in BUTTONS
    )


class ScreenPilotButton(ScreenPilotEntity, ButtonEntity):
    """Button for ScreenPilot."""

    entity_description: ScreenPilotButtonDescription

    def __init__(
        self,
        coordinator,
        api: ScreenPilotAPI,
        entry_id: str,
        description: ScreenPilotButtonDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, entry_id)
        self._api = api
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            # Special handling for load_start_url
            if self.entity_description.key == "load_start_url":
                startup_url = self.data.startup_url
                if startup_url:
                    await self._api.set_kiosk_url(startup_url)
            else:
                await self.entity_description.press_fn(self._api)

            if self.entity_description.refresh_after:
                await self.coordinator.async_request_refresh()
        except ScreenPilotError as err:
            raise HomeAssistantError(f"Failed to press {self.name}: {err}") from err
