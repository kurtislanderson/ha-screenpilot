"""Config flow for ScreenPilot integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TOKEN
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ScreenPilotAPI, ScreenPilotAuthError, ScreenPilotConnectionError
from .const import CONF_USE_HTTPS, DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_TOKEN): str,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Optional(CONF_USE_HTTPS, default=False): bool,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ScreenPilot."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            api = ScreenPilotAPI(
                session=session,
                host=user_input[CONF_HOST],
                token=user_input[CONF_TOKEN],
                use_https=user_input.get(CONF_USE_HTTPS, False),
            )

            try:
                await api.test_connection()
                system_info = await api.get_system_info()
            except ScreenPilotAuthError:
                errors["base"] = "invalid_auth"
            except ScreenPilotConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Set unique ID based on host
                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()

                # Use hostname from device if available
                title = (
                    user_input.get(CONF_NAME)
                    or system_info.get("hostname")
                    or user_input[CONF_HOST]
                )

                return self.async_create_entry(
                    title=title,
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
