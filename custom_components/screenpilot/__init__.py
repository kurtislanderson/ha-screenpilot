"""The ScreenPilot integration."""
from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
import async_timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_TOKEN,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    CONF_USE_HTTPS,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.CAMERA,
    Platform.SELECT,
    Platform.TEXT,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ScreenPilot from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Create API client
    api = ScreenPilotAPI(
        hass,
        entry.data[CONF_HOST],
        entry.data[CONF_TOKEN],
        entry.data.get(CONF_USE_HTTPS, False),
    )
    
    # Verify connection
    try:
        await api.test_connection()
    except Exception as err:
        raise ConfigEntryNotReady(f"Error connecting to ScreenPilot: {err}") from err
    
    # Create coordinators for different update intervals
    coordinators = {
        "system": DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=f"{entry.data[CONF_NAME]} System",
            update_method=api.get_system_info,
            update_interval=timedelta(seconds=30),
        ),
        "kiosk": DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=f"{entry.data[CONF_NAME]} Kiosk",
            update_method=api.get_kiosk_info,
            update_interval=timedelta(seconds=30),
        ),
        "service": DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=f"{entry.data[CONF_NAME]} Services",
            update_method=api.get_service_status,
            update_interval=timedelta(seconds=30),
        ),
        "cec": DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=f"{entry.data[CONF_NAME]} CEC",
            update_method=api.get_cec_status,
            update_interval=timedelta(seconds=30),
        ),
    }
    
    # Fetch initial data
    for coordinator in coordinators.values():
        await coordinator.async_config_entry_first_refresh()
    
    # Store data
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinators": coordinators,
        "name": entry.data[CONF_NAME],
    }
    
    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class ScreenPilotAPI:
    """API client for ScreenPilot."""
    
    def __init__(self, hass: HomeAssistant, host: str, token: str, use_https: bool = False) -> None:
        """Initialize the API client."""
        self.hass = hass
        self.host = host
        self.token = token
        self.use_https = use_https
        self._session = async_get_clientsession(hass)
        
    @property
    def base_url(self) -> str:
        """Get the base URL."""
        protocol = "https" if self.use_https else "http"
        return f"{protocol}://{self.host}"
        
    @property
    def headers(self) -> dict:
        """Get the headers for API requests."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        
    async def test_connection(self) -> bool:
        """Test the connection to ScreenPilot."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.get(
                    f"{self.base_url}/api/health/",
                    headers=self.headers,
                )
                response.raise_for_status()
                return True
        except Exception as err:
            _LOGGER.error("Failed to connect to ScreenPilot: %s", err)
            raise
            
    async def get_system_info(self) -> dict:
        """Get system information."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.get(
                    f"{self.base_url}/api/system/info/",
                    headers=self.headers,
                )
                response.raise_for_status()
                return await response.json()
        except Exception as err:
            raise UpdateFailed(f"Error fetching system info: {err}") from err
            
    async def get_kiosk_info(self) -> dict:
        """Get kiosk information."""
        try:
            data = {}
            
            # Get current URL
            async with async_timeout.timeout(10):
                response = await self._session.get(
                    f"{self.base_url}/api/kiosk/url/",
                    headers=self.headers,
                )
                response.raise_for_status()
                data.update(await response.json())
                
            # Get health status
            async with async_timeout.timeout(10):
                response = await self._session.get(
                    f"{self.base_url}/api/kiosk/health/",
                    headers=self.headers,
                )
                response.raise_for_status()
                data.update(await response.json())
                
            return data
        except Exception as err:
            raise UpdateFailed(f"Error fetching kiosk info: {err}") from err
            
    async def get_service_status(self) -> dict:
        """Get service status."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.get(
                    f"{self.base_url}/api/status/service_status/",
                    headers=self.headers,
                )
                response.raise_for_status()
                return await response.json()
        except Exception as err:
            raise UpdateFailed(f"Error fetching service status: {err}") from err
            
    async def get_cec_status(self) -> dict:
        """Get CEC status."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.get(
                    f"{self.base_url}/api/cec/status/",
                    headers=self.headers,
                )
                response.raise_for_status()
                return await response.json()
        except Exception as err:
            raise UpdateFailed(f"Error fetching CEC status: {err}") from err
            
    async def set_kiosk_url(self, url: str) -> bool:
        """Set the kiosk URL."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.put(
                    f"{self.base_url}/api/kiosk/url/",
                    headers=self.headers,
                    json={"url": url},
                )
                response.raise_for_status()
                return True
        except Exception as err:
            _LOGGER.error("Failed to set kiosk URL: %s", err)
            return False
            
    async def reload_page(self) -> bool:
        """Reload the current page."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.get(
                    f"{self.base_url}/api/kiosk/reload_currenturl/",
                    headers=self.headers,
                )
                response.raise_for_status()
                return True
        except Exception as err:
            _LOGGER.error("Failed to reload page: %s", err)
            return False
            
    async def restart_browser(self) -> bool:
        """Restart the browser."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.get(
                    f"{self.base_url}/api/kiosk/reload/",
                    headers=self.headers,
                )
                response.raise_for_status()
                return True
        except Exception as err:
            _LOGGER.error("Failed to restart browser: %s", err)
            return False
            
    async def clear_browser_data(self) -> bool:
        """Clear browser data."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.post(
                    f"{self.base_url}/api/kiosk/clear_data/",
                    headers=self.headers,
                )
                response.raise_for_status()
                return True
        except Exception as err:
            _LOGGER.error("Failed to clear browser data: %s", err)
            return False
            
    async def set_session_mode(self, mode: str) -> bool:
        """Set session mode."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.put(
                    f"{self.base_url}/api/kiosk/session_mode/",
                    headers=self.headers,
                    json={"mode": mode},
                )
                response.raise_for_status()
                return True
        except Exception as err:
            _LOGGER.error("Failed to set session mode: %s", err)
            return False
            
    async def send_cec_command(self, command: str) -> bool:
        """Send a CEC command."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.post(
                    f"{self.base_url}/api/cec/command/{command}/",
                    headers=self.headers,
                )
                response.raise_for_status()
                return True
        except Exception as err:
            _LOGGER.error("Failed to send CEC command: %s", err)
            return False
            
    async def reboot_system(self) -> bool:
        """Reboot the system."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.post(
                    f"{self.base_url}/api/system/reboot/",
                    headers=self.headers,
                )
                response.raise_for_status()
                return True
        except Exception as err:
            _LOGGER.error("Failed to reboot system: %s", err)
            return False
            
    async def control_service(self, service_name: str, action: str) -> bool:
        """Control a system service."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.post(
                    f"{self.base_url}/api/system/service/{service_name}/{action}/",
                    headers=self.headers,
                )
                response.raise_for_status()
                return True
        except Exception as err:
            _LOGGER.error("Failed to control service: %s", err)
            return False
            
    def get_screenshot_url(self) -> str:
        """Get the screenshot URL."""
        return f"{self.base_url}/api/kiosk/screenshot/?token={self.token}"