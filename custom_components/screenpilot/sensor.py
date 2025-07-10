"""Sensor platform for ScreenPilot integration."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    DOMAIN,
    ICON_CPU,
    ICON_MEMORY,
    ICON_DISK,
    ICON_UPTIME,
    ICON_BROWSER,
    ICON_HEARTBEAT,
    ICON_URL,
    ICON_SERVICE,
)

_LOGGER = logging.getLogger(__name__)

SENSOR_DESCRIPTIONS = [
    # System sensors
    SensorEntityDescription(
        key="cpu_percent",
        name="CPU",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_CPU,
    ),
    SensorEntityDescription(
        key="memory_percent",
        name="Memory",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_MEMORY,
    ),
    SensorEntityDescription(
        key="disk_percent",
        name="Disk",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_DISK,
    ),
    SensorEntityDescription(
        key="uptime",
        name="Uptime",
        icon=ICON_UPTIME,
    ),
    SensorEntityDescription(
        key="ip_address",
        name="IP Address",
        icon="mdi:ip-network",
    ),
    # Kiosk sensors
    SensorEntityDescription(
        key="current_url",
        name="Current URL",
        icon=ICON_URL,
    ),
    SensorEntityDescription(
        key="browser_status",
        name="Browser Status",
        icon=ICON_BROWSER,
    ),
    SensorEntityDescription(
        key="last_heartbeat",
        name="Last Heartbeat",
        icon=ICON_HEARTBEAT,
    ),
    SensorEntityDescription(
        key="session_mode",
        name="Session Mode",
        icon="mdi:lock",
    ),
    # Service sensors
    SensorEntityDescription(
        key="service_health",
        name="Service Health",
        icon=ICON_SERVICE,
    ),
    # CEC sensors
    SensorEntityDescription(
        key="tv_power_status",
        name="TV Power",
        icon="mdi:television",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ScreenPilot sensor platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinators = data["coordinators"]
    name = data["name"]
    
    entities = []
    
    # Add system sensors
    for description in SENSOR_DESCRIPTIONS:
        if description.key in ["cpu_percent", "memory_percent", "disk_percent", "uptime", "ip_address"]:
            entities.append(
                ScreenPilotSensor(
                    coordinators["system"],
                    description,
                    name,
                    config_entry.entry_id,
                )
            )
        elif description.key in ["current_url", "browser_status", "last_heartbeat", "session_mode"]:
            entities.append(
                ScreenPilotSensor(
                    coordinators["kiosk"],
                    description,
                    name,
                    config_entry.entry_id,
                )
            )
        elif description.key == "service_health":
            entities.append(
                ScreenPilotSensor(
                    coordinators["service"],
                    description,
                    name,
                    config_entry.entry_id,
                )
            )
        elif description.key == "tv_power_status":
            entities.append(
                ScreenPilotSensor(
                    coordinators["cec"],
                    description,
                    name,
                    config_entry.entry_id,
                )
            )
    
    async_add_entities(entities)


class ScreenPilotSensor(CoordinatorEntity, SensorEntity):
    """Representation of a ScreenPilot sensor."""
    
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        description: SensorEntityDescription,
        name: str,
        entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_name = f"{name} {description.name}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=name,
            manufacturer="ScreenPilot",
            model="Kiosk Display",
        )
        
    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
            
        key = self.entity_description.key
        
        # Handle different data structures
        if key == "cpu_percent":
            return self.coordinator.data.get("cpu_percent", 0)
        elif key == "memory_percent":
            memory = self.coordinator.data.get("memory", {})
            return memory.get("percent", 0) if memory else 0
        elif key == "disk_percent":
            disk = self.coordinator.data.get("disk", {})
            return disk.get("percent", 0) if disk else 0
        elif key == "uptime":
            uptime_seconds = self.coordinator.data.get("uptime", 0)
            return self._format_uptime(uptime_seconds)
        elif key == "ip_address":
            return self.coordinator.data.get("ip_address", "Unknown")
        elif key == "current_url":
            return self.coordinator.data.get("url", "Unknown")
        elif key == "browser_status":
            connected = self.coordinator.data.get("browser_connected", False)
            return "Connected" if connected else "Disconnected"
        elif key == "last_heartbeat":
            heartbeat_age = self.coordinator.data.get("heartbeat_age", 999)
            return self._format_heartbeat(heartbeat_age)
        elif key == "session_mode":
            return self.coordinator.data.get("session_mode", "normal")
        elif key == "service_health":
            all_healthy = self.coordinator.data.get("all_healthy", False)
            return "Healthy" if all_healthy else "Unhealthy"
        elif key == "tv_power_status":
            return self.coordinator.data.get("power_status", "unknown")
            
        return None
        
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if self.coordinator.data is None:
            return {}
            
        key = self.entity_description.key
        
        # Add relevant attributes based on sensor type
        if key == "service_health":
            services = self.coordinator.data.get("services", [])
            return {
                "services": {
                    service["name"]: {
                        "healthy": service.get("healthy", False),
                        "status": service.get("status", "unknown"),
                    }
                    for service in services
                }
            }
        elif key == "tv_power_status":
            return {
                "tv_present": self.coordinator.data.get("tv_present", False),
                "available_commands": self.coordinator.data.get("available_commands", []),
            }
        elif key == "browser_status":
            return {
                "last_heartbeat": self.coordinator.data.get("last_heartbeat", "Unknown"),
                "heartbeat_age": self.coordinator.data.get("heartbeat_age", 999),
            }
            
        return {}
        
    def _format_uptime(self, seconds: int) -> str:
        """Format uptime in seconds to human readable string."""
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
            
    def _format_heartbeat(self, seconds: int) -> str:
        """Format heartbeat age in seconds to human readable string."""
        if seconds < 60:
            return f"{seconds}s ago"
        elif seconds < 3600:
            return f"{seconds // 60}m ago"
        else:
            return f"{seconds // 3600}h ago"