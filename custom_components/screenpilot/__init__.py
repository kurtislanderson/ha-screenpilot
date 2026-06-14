"""The ScreenPilot integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TOKEN, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ScreenPilotAPI, ScreenPilotConnectionError, ScreenPilotError
from .const import (
    ATTR_COMMAND,
    ATTR_DATA_TYPE,
    ATTR_DISMISSIBLE,
    ATTR_HEIGHT,
    ATTR_HTML,
    ATTR_LEVEL,
    ATTR_SCRIPT,
    ATTR_TITLE,
    ATTR_URL,
    ATTR_WIDTH,
    CEC_COMMANDS,
    CLEAR_DATA_TYPES,
    CONF_USE_HTTPS,
    DOMAIN,
    SERVICE_CLEAR_DATA,
    SERVICE_EXECUTE_JS,
    SERVICE_LOAD_URL,
    SERVICE_SEND_CEC,
    SERVICE_SET_ZOOM,
    SERVICE_SHOW_OVERLAY,
)
from .coordinator import ScreenPilotCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CAMERA,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.TEXT,
]

# Track if services are registered
_SERVICES_REGISTERED = False


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ScreenPilot from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)
    api = ScreenPilotAPI(
        session=session,
        host=entry.data[CONF_HOST],
        token=entry.data[CONF_TOKEN],
        use_https=entry.data.get(CONF_USE_HTTPS, False),
    )

    # Verify connection
    try:
        await api.test_connection()
    except ScreenPilotConnectionError as err:
        raise ConfigEntryNotReady(f"Cannot connect to ScreenPilot: {err}") from err

    # Create coordinator
    coordinator = ScreenPilotCoordinator(
        hass=hass,
        api=api,
        name=entry.data.get(CONF_NAME, "ScreenPilot"),
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store data
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }

    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services (only once)
    await async_setup_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    global _SERVICES_REGISTERED  # noqa: PLW0603

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

        # If no more entries, unregister services
        if not hass.data[DOMAIN] and _SERVICES_REGISTERED:
            for service in [
                SERVICE_LOAD_URL,
                SERVICE_EXECUTE_JS,
                SERVICE_SEND_CEC,
                SERVICE_CLEAR_DATA,
                SERVICE_SET_ZOOM,
                SERVICE_SHOW_OVERLAY,
            ]:
                hass.services.async_remove(DOMAIN, service)
            _SERVICES_REGISTERED = False

    return unload_ok


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up ScreenPilot services."""
    global _SERVICES_REGISTERED  # noqa: PLW0603

    if _SERVICES_REGISTERED:
        return

    async def get_entries() -> list[tuple[str, ScreenPilotAPI, ScreenPilotCoordinator]]:
        """Get all configured entries."""
        entries = []
        for entry_id, data in hass.data.get(DOMAIN, {}).items():
            if isinstance(data, dict) and "api" in data:
                entries.append((entry_id, data["api"], data["coordinator"]))
        return entries

    async def handle_load_url(call: ServiceCall) -> None:
        """Handle load_url service."""
        url = call.data[ATTR_URL]
        entries = await get_entries()
        if not entries:
            raise HomeAssistantError("No ScreenPilot devices configured")

        errors = []
        for entry_id, api, coordinator in entries:
            try:
                await api.set_kiosk_url(url)
                await coordinator.async_request_refresh()
            except ScreenPilotError as err:
                errors.append(f"{entry_id}: {err}")
                _LOGGER.error("Failed to load URL on %s: %s", entry_id, err)

        if errors:
            raise HomeAssistantError(f"Failed on some devices: {', '.join(errors)}")

    async def handle_execute_js(call: ServiceCall) -> None:
        """Handle execute_javascript service."""
        script = call.data[ATTR_SCRIPT]
        entries = await get_entries()
        if not entries:
            raise HomeAssistantError("No ScreenPilot devices configured")

        errors = []
        for entry_id, api, _ in entries:
            try:
                await api.execute_javascript(script)
            except ScreenPilotError as err:
                errors.append(f"{entry_id}: {err}")
                _LOGGER.error("Failed to execute JS on %s: %s", entry_id, err)

        if errors:
            raise HomeAssistantError(f"Failed on some devices: {', '.join(errors)}")

    async def handle_send_cec(call: ServiceCall) -> None:
        """Handle send_cec_command service."""
        command = call.data[ATTR_COMMAND]
        entries = await get_entries()
        if not entries:
            raise HomeAssistantError("No ScreenPilot devices configured")

        errors = []
        for entry_id, api, coordinator in entries:
            try:
                await api.send_cec_command(command)
                await coordinator.async_request_refresh()
            except ScreenPilotError as err:
                errors.append(f"{entry_id}: {err}")
                _LOGGER.error("Failed to send CEC on %s: %s", entry_id, err)

        if errors:
            raise HomeAssistantError(f"Failed on some devices: {', '.join(errors)}")

    async def handle_clear_data(call: ServiceCall) -> None:
        """Handle clear_data service."""
        data_type = call.data.get(ATTR_DATA_TYPE, "all")
        entries = await get_entries()
        if not entries:
            raise HomeAssistantError("No ScreenPilot devices configured")

        errors = []
        for entry_id, api, _ in entries:
            try:
                await api.clear_data(data_type)
            except ScreenPilotError as err:
                errors.append(f"{entry_id}: {err}")
                _LOGGER.error("Failed to clear data on %s: %s", entry_id, err)

        if errors:
            raise HomeAssistantError(f"Failed on some devices: {', '.join(errors)}")

    async def handle_set_zoom(call: ServiceCall) -> None:
        """Handle set_zoom service."""
        level = call.data[ATTR_LEVEL]
        entries = await get_entries()
        if not entries:
            raise HomeAssistantError("No ScreenPilot devices configured")

        errors = []
        for entry_id, api, coordinator in entries:
            try:
                await api.set_zoom(level)
                await coordinator.async_request_refresh()
            except ScreenPilotError as err:
                errors.append(f"{entry_id}: {err}")
                _LOGGER.error("Failed to set zoom on %s: %s", entry_id, err)

        if errors:
            raise HomeAssistantError(f"Failed on some devices: {', '.join(errors)}")

    async def handle_show_overlay(call: ServiceCall) -> None:
        """Handle show_overlay service."""
        entries = await get_entries()
        if not entries:
            raise HomeAssistantError("No ScreenPilot devices configured")

        kwargs = {
            "url": call.data.get(ATTR_URL),
            "html": call.data.get(ATTR_HTML),
            "title": call.data.get(ATTR_TITLE),
            "dismissible": call.data.get(ATTR_DISMISSIBLE),
            "width": call.data.get(ATTR_WIDTH),
            "height": call.data.get(ATTR_HEIGHT),
        }

        errors = []
        for entry_id, api, coordinator in entries:
            try:
                await api.show_overlay(**kwargs)
                await coordinator.async_request_refresh()
            except ScreenPilotError as err:
                errors.append(f"{entry_id}: {err}")
                _LOGGER.error("Failed to show overlay on %s: %s", entry_id, err)

        if errors:
            raise HomeAssistantError(f"Failed on some devices: {', '.join(errors)}")

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_LOAD_URL,
        handle_load_url,
        schema=vol.Schema({vol.Required(ATTR_URL): cv.url}),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_EXECUTE_JS,
        handle_execute_js,
        schema=vol.Schema({vol.Required(ATTR_SCRIPT): cv.string}),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_CEC,
        handle_send_cec,
        schema=vol.Schema({vol.Required(ATTR_COMMAND): vol.In(CEC_COMMANDS)}),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEAR_DATA,
        handle_clear_data,
        schema=vol.Schema(
            {vol.Optional(ATTR_DATA_TYPE, default="all"): vol.In(CLEAR_DATA_TYPES)}
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_ZOOM,
        handle_set_zoom,
        schema=vol.Schema(
            {
                vol.Required(ATTR_LEVEL): vol.All(
                    vol.Coerce(int), vol.Range(min=25, max=500)
                )
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SHOW_OVERLAY,
        handle_show_overlay,
        schema=vol.Schema(
            {
                vol.Optional(ATTR_URL): cv.string,
                vol.Optional(ATTR_HTML): cv.string,
                vol.Optional(ATTR_TITLE): cv.string,
                vol.Optional(ATTR_DISMISSIBLE): cv.boolean,
                vol.Optional(ATTR_WIDTH): cv.string,
                vol.Optional(ATTR_HEIGHT): cv.string,
            }
        ),
    )

    _SERVICES_REGISTERED = True
