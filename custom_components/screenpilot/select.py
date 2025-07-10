"""Select platform for ScreenPilot integration."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, SESSION_MODES, CEC_COMMANDS

_LOGGER = logging.getLogger(__name__)

SELECT_DESCRIPTIONS = [
    SelectEntityDescription(
        key="session_mode",
        name="Session Mode",
        options=SESSION_MODES,
        icon="mdi:lock",
    ),
    SelectEntityDescription(
        key="cec_command",
        name="CEC Command",
        options=CEC_COMMANDS,
        icon="mdi:remote",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ScreenPilot select platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    api = data["api"]
    coordinator = data["coordinators"]["kiosk"]
    name = data["name"]
    
    entities = []
    for description in SELECT_DESCRIPTIONS:
        if description.key == "session_mode":
            entities.append(
                ScreenPilotSessionModeSelect(
                    coordinator,
                    api,
                    description,
                    name,
                    config_entry.entry_id,
                )
            )
        elif description.key == "cec_command":
            entities.append(
                ScreenPilotCECSelect(
                    api,
                    description,
                    name,
                    config_entry.entry_id,
                )
            )
    
    async_add_entities(entities)


class ScreenPilotSessionModeSelect(CoordinatorEntity, SelectEntity):
    """Representation of a ScreenPilot session mode selector."""
    
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        api,
        description: SelectEntityDescription,
        name: str,
        entry_id: str,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._api = api
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_name = f"{name} {description.name}"
        self._attr_options = list(description.options)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=name,
            manufacturer="ScreenPilot",
            model="Kiosk Display",
        )
        
    @property
    def current_option(self) -> str | None:
        """Return the current session mode."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("session_mode", "normal")
        
    async def async_select_option(self, option: str) -> None:
        """Change the session mode."""
        await self._api.set_session_mode(option)
        await self.coordinator.async_request_refresh()


class ScreenPilotCECSelect(SelectEntity):
    """Representation of a ScreenPilot CEC command selector."""
    
    def __init__(
        self,
        api,
        description: SelectEntityDescription,
        name: str,
        entry_id: str,
    ) -> None:
        """Initialize the select entity."""
        self._api = api
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_name = f"{name} {description.name}"
        self._attr_options = list(description.options)
        self._attr_current_option = None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=name,
            manufacturer="ScreenPilot",
            model="Kiosk Display",
        )
        
    async def async_select_option(self, option: str) -> None:
        """Send the selected CEC command."""
        await self._api.send_cec_command(option)
        # Reset selection after sending command
        self._attr_current_option = None
        self.async_write_ha_state()