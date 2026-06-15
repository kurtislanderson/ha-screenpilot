# ScreenPilot Home Assistant Integration

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Control your ScreenPilot kiosk display from Home Assistant.

## Features

- **Browser Control**: Navigate URLs, reload/hard-refresh, zoom, clear data, session mode
- **Navigation Overlay**: Show/hide a modal panel, Home/Back navigation, overlay-visible status, plus severity-styled alert banners (auto + manual)
- **TV Control**: Power on/off, volume, HDMI input switching via CEC
- **Monitoring**: System health, CPU, memory, disk, per-service status, network, reboot schedule
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
- System Problem, Browser Connected, Browser Problem
- Services Problem, Kiosk Service, Web Console Service, CEC / HDMI Service
- Network Connected
- Overlay Visible
- TV Present, TV Power

### Sensors
- CPU, Memory, Disk usage
- Uptime, IP Address
- Current URL, Startup URL
- Zoom Level, Session Mode
- Health Status, Heartbeat Age, Last Heartbeat, Chrome Version
- Services Active, Display Resolution, Reboot Schedule
- TV Power Status, CEC Detection Status, Last CEC Command
- ScreenPilot Version, Display Stack (diagnostic) — the running app version and
  display stack (`wayland` = v2, `x11` = v1). Also surfaced as the device
  `sw_version`, e.g. `2.0.0 (wayland)`. Shows `unknown` for ScreenPilot builds
  predating the `/api/system/info/` version fields.

### Controls
- **Switch**: TV Power
- **Buttons**: Reload Page, Hard Refresh, Load Start URL, Restart Browser,
  Clear Cache, Clear All Data, Reboot Device
- **Overlay buttons**: Overlay Home, Overlay Back, Overlay Hide
- **CEC buttons**: Detect CEC Capabilities, Power On, Power Off, Make Active
  Source, Make Inactive Source, Volume Up, Volume Down, Mute Toggle
- **Selects**: HDMI Input, Session Mode
- **Number**: Zoom Level slider
- **Text**: Display URL, Startup URL

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
| `screenpilot.show_overlay` | Show a modal overlay panel (`url`/`html`/`title`/`dismissible`/`width`/`height`) |
| `screenpilot.raise_alert` | Raise/update an overlay alert banner (`id`/`severity`/`message`/`ttl`/`dismissible`) |
| `screenpilot.clear_alert` | Clear an overlay alert by `id` |
| `screenpilot.set_alert_source` | Enable/disable an automatic alert source (`wifi_fallback`/`offline`/`service_degraded`) |

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

# Show a doorbell snapshot overlay without navigating away
automation:
  - alias: "Doorbell overlay"
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door
        to: "on"
    action:
      - service: screenpilot.show_overlay
        data:
          url: "http://homeassistant.local:8123/lovelace/doorbell"
          title: "Front Door"
          dismissible: true
          width: "80vw"
          height: "80vh"
```

## License

MIT
