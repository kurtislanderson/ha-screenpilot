"""Button platform for ScreenPilot integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

BUTTON_DESCRIPTIONS = [
    ButtonEntityDescription(
        key="reload_page",
        name="Reload Page",
        icon="mdi:refresh",
    ),
    ButtonEntityDescription(
        key="restart_browser",
        name="Restart Browser",
        icon="mdi:restart",
    ),
    ButtonEntityDescription(
        key="clear_browser_data",
        name="Clear Browser Data",
        icon="mdi:delete-sweep",
    ),
    ButtonEntityDescription(
        key="reboot_system",
        name="Reboot System",
        icon="mdi:restart-alert",
    ),
    # CEC buttons
    ButtonEntityDescription(
        key="volume_up",
        name="Volume Up",
        icon="mdi:volume-plus",
    ),
    ButtonEntityDescription(
        key="volume_down",
        name="Volume Down",
        icon="mdi:volume-minus",
    ),
    ButtonEntityDescription(
        key="mute",
        name="Mute",
        icon="mdi:volume-mute",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ScreenPilot button platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    api = data["api"]
    name = data["name"]
    
    entities = []
    for description in BUTTON_DESCRIPTIONS:
        entities.append(
            ScreenPilotButton(
                api,
                description,
                name,
                config_entry.entry_id,
            )
        )
    
    async_add_entities(entities)


class ScreenPilotButton(ButtonEntity):
    """Representation of a ScreenPilot button."""
    
    def __init__(
        self,
        api,
        description: ButtonEntityDescription,
        name: str,
        entry_id: str,
    ) -> None:
        """Initialize the button."""
        self._api = api
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_name = f"{name} {description.name}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=name,
            manufacturer="ScreenPilot",
            model="Kiosk Display",
        )
        
    async def async_press(self) -> None:
        """Handle the button press."""
        key = self.entity_description.key
        
        if key == "reload_page":
            await self._api.reload_page()
        elif key == "restart_browser":
            await self._api.restart_browser()
        elif key == "clear_browser_data":
            await self._api.clear_browser_data()
        elif key == "reboot_system":
            await self._api.reboot_system()
        elif key in ["volume_up", "volume_down", "mute"]:
            await self._api.send_cec_command(key)