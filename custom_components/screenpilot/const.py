"""Constants for the ScreenPilot integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "screenpilot"

# Configuration
CONF_USE_HTTPS: Final = "use_https"
DEFAULT_NAME: Final = "ScreenPilot"
DEFAULT_PORT: Final = 80
UPDATE_INTERVAL: Final = 30

# Services
SERVICE_LOAD_URL: Final = "load_url"
SERVICE_EXECUTE_JS: Final = "execute_javascript"
SERVICE_SEND_CEC: Final = "send_cec_command"
SERVICE_CLEAR_DATA: Final = "clear_data"
SERVICE_SET_ZOOM: Final = "set_zoom"
SERVICE_SHOW_OVERLAY: Final = "show_overlay"

# Attributes
ATTR_URL: Final = "url"
ATTR_SCRIPT: Final = "script"
ATTR_COMMAND: Final = "command"
ATTR_DATA_TYPE: Final = "data_type"
ATTR_LEVEL: Final = "level"
ATTR_HTML: Final = "html"
ATTR_TITLE: Final = "title"
ATTR_DISMISSIBLE: Final = "dismissible"
ATTR_WIDTH: Final = "width"
ATTR_HEIGHT: Final = "height"

# CEC Commands
CEC_COMMANDS: Final = [
    "power_on",
    "power_off",
    "power_toggle",
    "volume_up",
    "volume_down",
    "mute_toggle",
    "active_source",
    "inactive_source",
    "input_hdmi1",
    "input_hdmi2",
    "input_hdmi3",
    "input_hdmi4",
]

# HDMI Inputs
HDMI_INPUTS: Final = {
    "HDMI 1": "input_hdmi1",
    "HDMI 2": "input_hdmi2",
    "HDMI 3": "input_hdmi3",
    "HDMI 4": "input_hdmi4",
}

# Session Modes
SESSION_MODES: Final = ["persistent", "temporary", "custom"]

# Clear Data Types
CLEAR_DATA_TYPES: Final = ["cache", "cookies", "localStorage", "all"]
