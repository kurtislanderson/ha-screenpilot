"""Constants for the ScreenPilot integration."""
from datetime import timedelta

DOMAIN = "screenpilot"

# Configuration
CONF_USE_HTTPS = "use_https"
DEFAULT_NAME = "ScreenPilot"
DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)

# Service Names
SERVICE_SET_URL = "set_url"
SERVICE_RELOAD_PAGE = "reload_page"
SERVICE_RESTART_BROWSER = "restart_browser"
SERVICE_CLEAR_DATA = "clear_browser_data"
SERVICE_SET_SESSION_MODE = "set_session_mode"
SERVICE_SEND_CEC_COMMAND = "send_cec_command"
SERVICE_REBOOT = "reboot_system"
SERVICE_CONTROL_SERVICE = "control_service"

# Attributes
ATTR_URL = "url"
ATTR_MODE = "mode"
ATTR_COMMAND = "command"
ATTR_SERVICE_NAME = "service_name"
ATTR_ACTION = "action"

# CEC Commands
CEC_COMMANDS = [
    "power_on",
    "power_off",
    "power_toggle",
    "volume_up",
    "volume_down",
    "mute",
    "input_hdmi1",
    "input_hdmi2",
    "input_hdmi3",
    "input_hdmi4",
]

# Session Modes
SESSION_MODES = [
    "normal",
    "persistent",
]

# Service Actions
SERVICE_ACTIONS = [
    "start",
    "stop",
    "restart",
    "status",
]

# Icons
ICON_DISPLAY = "mdi:monitor"
ICON_TV = "mdi:television"
ICON_CPU = "mdi:cpu-64-bit"
ICON_MEMORY = "mdi:memory"
ICON_DISK = "mdi:harddisk"
ICON_UPTIME = "mdi:timer-outline"
ICON_BROWSER = "mdi:web"
ICON_HEARTBEAT = "mdi:heart-pulse"
ICON_SERVICE = "mdi:cog"
ICON_URL = "mdi:link"
ICON_SESSION = "mdi:lock"