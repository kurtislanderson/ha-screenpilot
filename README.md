# ScreenPilot Home Assistant Integration

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Control your ScreenPilot kiosk display from Home Assistant.

## Features

- **Browser Control**: Navigate URLs, reload pages, control zoom level
- **TV Control**: Power on/off, volume, HDMI input switching via CEC
- **Monitoring**: System health, CPU, memory, disk usage, service status
- **Screenshots**: Live display capture

## Installation

### HACS (Recommended)

1. Add this repository as a custom repository in HACS
2. Search for "ScreenPilot" and install
3. Restart Home Assistant
4. Add the integration via Settings > Devices & Services

### Manual

1. Copy `custom_components/screenpilot` to your Home Assistant config directory
2. Restart Home Assistant
3. Add the integration via Settings > Devices & Services

## Configuration

You will need:
- **Host**: IP address or hostname of your ScreenPilot device
- **API Token**: The bearer token from your ScreenPilot installation

## Entities

### Binary Sensors
- System Problem
- Browser Connected
- TV Present
- TV Power
- Service Status

### Sensors
- CPU, Memory, Disk usage
- Current URL, Startup URL
- Zoom Level
- Health Status
- Heartbeat Age
- ScreenPilot Version, Display Stack (diagnostic) — the running app version and
  display stack (`wayland` = v2, `x11` = v1). Also surfaced as the device
  `sw_version`, e.g. `2.0.0 (wayland)`. Shows `unknown` for ScreenPilot builds
  predating the `/api/system/info/` version fields.

### Controls
- TV Power Switch
- Screen Power Switch
- Reload/Hard Refresh buttons
- Volume Up/Down/Mute buttons
- HDMI Input selector
- Zoom Level slider
- Display URL text input

### Camera
- Live screenshot of the kiosk display

## Services

| Service | Description |
|---------|-------------|
| `screenpilot.load_url` | Navigate to a URL |
| `screenpilot.execute_javascript` | Run JavaScript |
| `screenpilot.send_cec_command` | Send CEC command |
| `screenpilot.clear_data` | Clear browser data |
| `screenpilot.set_zoom` | Set zoom level |

## Example Automations

```yaml
# Turn on TV when Home Assistant starts
automation:
  - alias: "Turn on kiosk TV"
    trigger:
      - platform: homeassistant
        event: start
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.screenpilot_tv_power

# Display weather dashboard during the day
automation:
  - alias: "Show weather dashboard"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: screenpilot.load_url
        data:
          url: "http://homeassistant.local:8123/lovelace/weather"
```

## License

MIT
