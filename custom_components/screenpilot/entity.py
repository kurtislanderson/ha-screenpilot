"""Base entity for ScreenPilot."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ScreenPilotCoordinator, ScreenPilotData


# Default data for when coordinator hasn't fetched yet
_DEFAULT_DATA = ScreenPilotData()


class ScreenPilotEntity(CoordinatorEntity[ScreenPilotCoordinator]):
    """Base entity for ScreenPilot."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ScreenPilotCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._entry_id = entry_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self.coordinator.device_name,
            manufacturer="ScreenPilot",
            model="Kiosk Display",
            sw_version="1.0.0",
            configuration_url=self.coordinator.api.base_url,
        )

    @property
    def data(self) -> ScreenPilotData:
        """Return coordinator data with fallback to defaults."""
        if self.coordinator.data is None:
            return _DEFAULT_DATA
        return self.coordinator.data
