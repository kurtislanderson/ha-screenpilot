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
        # Report the live ScreenPilot app version (and which display stack it is
        # driving) as the device sw_version, e.g. "2.0.0 (wayland)". Falls back
        # to "unknown" on a Pi too old to expose /api/system/info version fields.
        data = self.coordinator.data
        version = data.screenpilot_version if data else "unknown"
        stack = data.display_stack if data else "unknown"
        if stack and stack != "unknown":
            sw_version = f"{version} ({stack})"
        else:
            sw_version = version
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self.coordinator.device_name,
            manufacturer="ScreenPilot",
            model="Kiosk Display",
            sw_version=sw_version,
            configuration_url=self.coordinator.api.base_url,
        )

    @property
    def data(self) -> ScreenPilotData:
        """Return coordinator data with fallback to defaults."""
        if self.coordinator.data is None:
            return _DEFAULT_DATA
        return self.coordinator.data
