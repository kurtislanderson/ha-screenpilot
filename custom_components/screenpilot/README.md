# ScreenPilot Home Assistant Integration

A custom Home Assistant integration for controlling ScreenPilot kiosk displays.

## Features

- **Multiple Device Support**: Add and control multiple ScreenPilot devices from one Home Assistant instance
- **Auto-discovery**: Automatic entity creation for each device
- **Real-time Updates**: Polling-based updates with configurable intervals
- **Full API Coverage**: All ScreenPilot API endpoints are accessible

## Entities Created

For each ScreenPilot device, the following entities are automatically created:

### Sensors
- **CPU Usage** - Current CPU utilization percentage
- **Memory Usage** - Current memory utilization percentage  
- **Disk Usage** - Current disk utilization percentage
- **Uptime** - System uptime formatted as human-readable string
- **IP Address** - Current IP address of the device
- **Current URL** - The URL currently displayed
- **Browser Status** - Connected/Disconnected status
- **Last Heartbeat** - Time since last browser heartbeat
- **Session Mode** - Current browser session mode (normal/persistent)
- **Service Health** - Overall health status of all services
- **TV Power** - Current TV power status (on/off/unknown)

### Controls
- **TV Power Switch** - Turn the connected TV on/off via CEC
- **URL Text Input** - Enter a URL to navigate to
- **Session Mode Select** - Choose between normal and persistent sessions
- **CEC Command Select** - Send CEC commands to the TV

### Buttons
- **Reload Page** - Refresh the current page
- **Restart Browser** - Restart the browser service
- **Clear Browser Data** - Clear all cookies, cache, and browser data
- **Reboot System** - Reboot the entire ScreenPilot device
- **Volume Up/Down** - Control TV volume via CEC
- **Mute** - Toggle TV mute via CEC

### Camera
- **Display Screenshot** - Live view of what's currently displayed

## Installation

### HACS (Recommended)

1. Add this repository as a custom repository in HACS
2. Search for "ScreenPilot" in HACS
3. Install the integration
4. Restart Home Assistant

### Manual Installation

1. Copy the `screenpilot` directory to your `custom_components` folder
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "ScreenPilot"
4. Enter the connection details:
   - **Host**: IP address and port (e.g., `192.168.1.100:8000`)
   - **API Token**: Your ScreenPilot API token
   - **Name**: Friendly name for this device
   - **Use HTTPS**: Check if using SSL/TLS

## Services

The integration provides the following services:

### screenpilot.set_url
Navigate to a specific URL
```yaml
service: screenpilot.set_url
target:
  entity_id: text.living_room_display_url
data:
  url: "https://example.com"
```

### screenpilot.reload_page
Reload the current page
```yaml
service: screenpilot.reload_page
target:
  entity_id: button.living_room_display_reload_page
```

### screenpilot.set_session_mode
Change browser session mode
```yaml
service: screenpilot.set_session_mode
target:
  entity_id: select.living_room_display_session_mode
data:
  mode: "persistent"
```

### screenpilot.send_cec_command
Send CEC command to TV
```yaml
service: screenpilot.send_cec_command
target:
  entity_id: select.living_room_display_cec_command
data:
  command: "volume_up"
```

### screenpilot.control_service
Control system services
```yaml
service: screenpilot.control_service
target:
  device_id: YOUR_DEVICE_ID
data:
  service_name: "screenpilot-kiosk"
  action: "restart"
```

## Automation Examples

### Show Weather in the Morning
```yaml
automation:
  - alias: "ScreenPilot Morning Weather"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.living_room_display_tv
      - delay:
          seconds: 5
      - service: text.set_value
        target:
          entity_id: text.living_room_display_url
        data:
          value: "https://weather.com"
```

### Turn Off TV at Night
```yaml
automation:
  - alias: "ScreenPilot TV Off at Night"
    trigger:
      - platform: time
        at: "23:00:00"
    condition:
      - condition: state
        entity_id: switch.living_room_display_tv
        state: "on"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.living_room_display_tv
```

### Alert on Browser Disconnect
```yaml
automation:
  - alias: "ScreenPilot Browser Disconnected Alert"
    trigger:
      - platform: state
        entity_id: sensor.living_room_display_browser_status
        to: "Disconnected"
        for:
          minutes: 5
    action:
      - service: notify.mobile_app
        data:
          title: "ScreenPilot Alert"
          message: "Browser disconnected on Living Room Display"
```

## Dashboard Card Example

```yaml
type: vertical-stack
cards:
  - type: entities
    title: ScreenPilot Control
    entities:
      - entity: sensor.living_room_display_browser_status
      - entity: text.living_room_display_url
      - entity: select.living_room_display_session_mode
      
  - type: horizontal-stack
    cards:
      - type: button
        entity: switch.living_room_display_tv
        tap_action:
          action: toggle
      - type: button
        entity: button.living_room_display_reload_page
      - type: button
        entity: button.living_room_display_restart_browser
        
  - type: picture-entity
    entity: camera.living_room_display_display
    camera_view: live
    
  - type: entities
    title: System Stats
    entities:
      - entity: sensor.living_room_display_cpu
      - entity: sensor.living_room_display_memory
      - entity: sensor.living_room_display_uptime
```

## Multiple Device Support

You can add multiple ScreenPilot devices through the UI. Each device will have its own set of entities with unique names based on the device name you provide during setup.

Example with two devices:
- `sensor.living_room_display_cpu`
- `sensor.kitchen_display_cpu`

## Troubleshooting

### Connection Failed
- Verify the host IP and port are correct
- Check that the API token is valid
- Ensure ScreenPilot is running and accessible
- Check firewall rules

### Entities Not Updating
- Check the logs for API errors
- Verify the ScreenPilot services are running
- Try reloading the integration

### Screenshot Not Working
- Ensure the browser service is running
- Check that the screenshot endpoint is accessible
- Verify authentication is working

## Development

To contribute or modify:

1. Clone the repository
2. Make changes in the `custom_components/screenpilot` directory
3. Test with a development Home Assistant instance
4. Submit a pull request

## License

This integration is part of the ScreenPilot project and follows the same license terms.