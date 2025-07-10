# ScreenPilot Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/kurtislanderson/screenpilot-homeassistant.svg)](https://github.com/kurtislanderson/screenpilot-homeassistant/releases)
[![License](https://img.shields.io/github/license/kurtislanderson/screenpilot-homeassistant.svg)](LICENSE)

Complete Home Assistant integration for [ScreenPilot](https://github.com/kurtislanderson/ScreenPilot) kiosk displays with support for multiple devices, full API coverage, and easy setup.

## 🚀 Installation

### HACS (Recommended)

1. **Add as custom repository:**
   - Open HACS in Home Assistant
   - Go to "Integrations" section
   - Click menu (3 dots) → "Custom repositories"
   - Add `https://github.com/kurtislanderson/screenpilot-homeassistant`
   - Category: "Integration"
   - Click "Add"

2. **Install the integration:**
   - Search for "ScreenPilot" in HACS
   - Click "Download"
   - Restart Home Assistant

3. **Configure via UI:**
   - Go to Settings → Devices & Services
   - Click "+ ADD INTEGRATION"
   - Search for "ScreenPilot"
   - Enter connection details:
     - **Host**: IP and port (e.g., `192.168.1.100` for production, `192.168.1.100:8000` for dev)
     - **API Token**: Your token (default: `dev-token-12345`)
     - **Name**: Friendly name (e.g., "Living Room Display")

### Manual Installation

1. Download the `custom_components/screenpilot` directory from this repository
2. Copy it to your Home Assistant `custom_components` directory
3. Restart Home Assistant
4. Configure via UI (same as step 3 above)

### Features

✅ **Complete API Coverage** - All endpoints implemented  
✅ **Multiple Device Support** - Add unlimited ScreenPilot instances  
✅ **Auto Entity Creation** - 23 entities per device  
✅ **Device Grouping** - All entities organized under one device  
✅ **Service Definitions** - Native Home Assistant services  
✅ **Efficient Updates** - Separate coordinators for different data types

See [custom_components/screenpilot/README.md](custom_components/screenpilot/README.md) for detailed documentation.

## 📦 What You Get Per Device

- **11 Sensors**: CPU, Memory, Disk, URL, Browser Status, etc.
- **4 Controls**: TV Switch, URL Input, Session Mode, CEC Commands
- **7 Buttons**: Reload, Restart, Clear Data, Volume controls, etc.
- **1 Camera**: Live screenshot
- **7 Services**: Full API control

## 🔧 Manual Configuration (Alternative)

For manual YAML configuration, see the examples in the `examples/` directory:
- `configuration_manual.yaml` - Single device setup
- `configuration_multi.yaml` - Multiple devices
- `automations.yaml` - Automation examples
- `lovelace-card.yaml` - Dashboard examples

## 📋 Prerequisites

1. **ScreenPilot running** and accessible from Home Assistant
2. **API token** from ScreenPilot (default: `dev-token-12345`)
3. **Network connectivity** between HA and ScreenPilot

### Port Configuration
- **Production** (on Pi): Use port 80 (nginx proxy) - e.g., `192.168.1.100`
- **Development**: Use port 8000 - e.g., `192.168.1.100:8000`

## 🧪 Testing Your Setup

Use the included test script to verify connectivity:

```bash
cd home_assistant/scripts
./test_api.sh [HOST] [TOKEN]

# Examples:
./test_api.sh 192.168.1.100 dev-token-12345        # Production
./test_api.sh 192.168.1.100:8000 dev-token-12345   # Development
```

## 🎯 Multiple Device Support

The custom integration fully supports multiple ScreenPilot instances:

```yaml
# Device 1: Living Room
Host: 192.168.1.100
Name: "Living Room Display"
Entities created:
  - sensor.living_room_display_cpu
  - switch.living_room_display_tv
  - camera.living_room_display_display
  ... (23 total)

# Device 2: Kitchen
Host: 192.168.1.101
Name: "Kitchen Display"
Entities created:
  - sensor.kitchen_display_cpu
  - switch.kitchen_display_tv
  - camera.kitchen_display_display
  ... (23 total)
```

## 📊 API Endpoints Coverage

### System Control ✅
- `/api/health/` - Connection test
- `/api/system/info/` - System information
- `/api/system/reboot/` - System reboot
- `/api/system/logs/` - System logs
- `/api/system/service/<service>/<action>/` - Service control

### Kiosk/Browser Control ✅
- `/api/kiosk/url/` - Get/Set current URL
- `/api/kiosk/startup_url/` - Get/Set startup URL
- `/api/kiosk/reload/` - Restart browser
- `/api/kiosk/reload_currenturl/` - Reload current page
- `/api/kiosk/screenshot/` - Get screenshot
- `/api/kiosk/heartbeat/` - Browser heartbeat
- `/api/kiosk/health/` - Browser health status
- `/api/kiosk/clear_data/` - Clear browser data
- `/api/kiosk/session_mode/` - Get/Set session mode

### CEC/TV Control ✅
- `/api/cec/status/` - TV status and presence
- `/api/cec/commands/` - List available commands
- `/api/cec/command/<command>/` - Send CEC commands

### Service Status ✅
- `/api/status/service_status/` - All service statuses

## 🏗️ Example Configuration (Manual)

For manual YAML configuration, here's a basic example:

```yaml
rest_command:
  # Kiosk control
  screenpilot_set_url:
    url: "http://{{ host }}/api/kiosk/url/"  # Add :8000 for development
    method: PUT
    headers:
      Authorization: "Bearer {{ token }}"
      Content-Type: "application/json"
    payload: '{"url": "{{ url }}"}'
    
  screenpilot_reload_page:
    url: "http://{{ host }}/api/kiosk/reload_currenturl/"
    method: GET
    headers:
      Authorization: "Bearer {{ token }}"
      
  screenpilot_restart_browser:
    url: "http://{{ host }}/api/kiosk/reload/"
    method: GET
    headers:
      Authorization: "Bearer {{ token }}"
    
  # CEC/TV control
  screenpilot_cec_command:
    url: "http://{{ host }}/api/cec/command/{{ command }}/"
    method: POST
    headers:
      Authorization: "Bearer {{ token }}"
    
  # System control
  screenpilot_reboot:
    url: "http://{{ host }}/api/system/reboot/"
    method: POST
    headers:
      Authorization: "Bearer {{ token }}"
```

### 2. REST Sensors

```yaml
sensor:
  - platform: rest
    name: "ScreenPilot Status"
    resource: "http://YOUR_SCREENPILOT_IP/api/system/info/"  # Production (port 80)
    # For development use: "http://YOUR_SCREENPILOT_IP:8000/api/system/info/"
    method: GET
    headers:
      Authorization: "Bearer YOUR_API_TOKEN"
    value_template: "{{ value_json.hostname }}"
    json_attributes:
      - hostname
      - os_version
      - ip_address
      - platform
      - cpu_percent
      - memory
      - disk
      - uptime
    scan_interval: 30
    
  - platform: rest
    name: "ScreenPilot Display URL"
    resource: "http://YOUR_SCREENPILOT_IP/api/kiosk/url/"  # Production
    # For development use: "http://YOUR_SCREENPILOT_IP:8000/api/kiosk/url/"
    method: GET
    headers:
      Authorization: "Bearer YOUR_API_TOKEN"
    value_template: "{{ value_json.url }}"
    scan_interval: 60
    
  - platform: rest
    name: "ScreenPilot TV Status"
    resource: "http://YOUR_SCREENPILOT_IP/api/cec/status/"  # Production
    # For development use: "http://YOUR_SCREENPILOT_IP:8000/api/cec/status/"
    method: GET
    headers:
      Authorization: "Bearer YOUR_API_TOKEN"
    value_template: "{{ value_json.power_status }}"
    json_attributes:
      - tv_present
      - power_status
      - available_commands
    scan_interval: 30
```

### 3. Template Sensors (for better formatting)

```yaml
template:
  - sensor:
      - name: "ScreenPilot CPU Usage"
        unit_of_measurement: "%"
        state: "{{ state_attr('sensor.screenpilot_status', 'cpu_percent') | round(1) }}"
        
      - name: "ScreenPilot Memory Usage"
        unit_of_measurement: "%"
        state: "{{ state_attr('sensor.screenpilot_status', 'memory')['percent'] | round(1) }}"
        
      - name: "ScreenPilot Disk Usage"
        unit_of_measurement: "%"
        state: "{{ state_attr('sensor.screenpilot_status', 'disk')['percent'] | round(1) }}"
        
      - name: "ScreenPilot Uptime"
        state: >
          {% set uptime = state_attr('sensor.screenpilot_status', 'uptime') | int %}
          {% set days = (uptime // 86400) %}
          {% set hours = ((uptime % 86400) // 3600) %}
          {% set minutes = ((uptime % 3600) // 60) %}
          {% if days > 0 %}
            {{ days }}d {{ hours }}h {{ minutes }}m
          {% elif hours > 0 %}
            {{ hours }}h {{ minutes }}m
          {% else %}
            {{ minutes }}m
          {% endif %}
```

### 4. Switches for TV Control

```yaml
switch:
  - platform: template
    switches:
      screenpilot_tv:
        friendly_name: "ScreenPilot TV"
        value_template: "{{ is_state('sensor.screenpilot_tv_status', 'on') }}"
        turn_on:
          service: rest_command.screenpilot_cec_command
          data:
            host: "YOUR_SCREENPILOT_IP"  # Add :8000 for development
            token: "YOUR_API_TOKEN"
            command: "power_on"
        turn_off:
          service: rest_command.screenpilot_cec_command
          data:
            host: "YOUR_SCREENPILOT_IP"  # Add :8000 for development
            token: "YOUR_API_TOKEN"
            command: "power_off"
        icon_template: >
          {% if is_state('sensor.screenpilot_tv_status', 'on') %}
            mdi:television
          {% else %}
            mdi:television-off
          {% endif %}
```

### 5. Camera for Screenshots

```yaml
camera:
  - platform: generic
    name: "ScreenPilot Display"
    still_image_url: "http://YOUR_SCREENPILOT_IP/api/kiosk/screenshot/"  # Production
    # For development use: "http://YOUR_SCREENPILOT_IP:8000/api/kiosk/screenshot/"
    scan_interval: 30
```

See `examples/` directory for complete configuration examples including:
- Multi-instance setup
- Automation examples
- Dashboard cards
- Input helpers

```yaml
input_select:
  screenpilot_quick_urls:
    name: "Quick URLs"
    options:
      - "Home Assistant"
      - "Weather"
      - "News"
      - "YouTube"
      - "Custom"
    initial: "Home Assistant"
    
input_text:
  screenpilot_custom_url:
    name: "Custom URL"
    initial: "https://example.com"
```

## 🤖 Automation Examples

### 1. Set URL Based on Selection

```yaml
automation:
  - alias: "ScreenPilot Set Quick URL"
    trigger:
      - platform: state
        entity_id: input_select.screenpilot_quick_urls
    action:
      - choose:
          - conditions:
              - condition: state
                entity_id: input_select.screenpilot_quick_urls
                state: "Home Assistant"
            sequence:
              - service: rest_command.screenpilot_set_url
                data:
                  host: "YOUR_SCREENPILOT_IP"
                  token: "YOUR_API_TOKEN"
                  url: "http://YOUR_HA_IP:8123/lovelace"
          
          - conditions:
              - condition: state
                entity_id: input_select.screenpilot_quick_urls
                state: "Weather"
            sequence:
              - service: rest_command.screenpilot_set_url
                data:
                  host: "YOUR_SCREENPILOT_IP"
                  token: "YOUR_API_TOKEN"
                  url: "https://weather.com"
          
          - conditions:
              - condition: state
                entity_id: input_select.screenpilot_quick_urls
                state: "News"
            sequence:
              - service: rest_command.screenpilot_set_url
                data:
                  host: "YOUR_SCREENPILOT_IP"
                  token: "YOUR_API_TOKEN"
                  url: "https://news.google.com"
          
          - conditions:
              - condition: state
                entity_id: input_select.screenpilot_quick_urls
                state: "YouTube"
            sequence:
              - service: rest_command.screenpilot_set_url
                data:
                  host: "YOUR_SCREENPILOT_IP"
                  token: "YOUR_API_TOKEN"
                  url: "https://youtube.com/tv"
          
          - conditions:
              - condition: state
                entity_id: input_select.screenpilot_quick_urls
                state: "Custom"
            sequence:
              - service: rest_command.screenpilot_set_url
                data:
                  host: "YOUR_SCREENPILOT_IP"
                  token: "YOUR_API_TOKEN"
                  url: "{{ states('input_text.screenpilot_custom_url') }}"
```

### 2. Turn Off TV at Night

```yaml
automation:
  - alias: "ScreenPilot TV Off at Night"
    trigger:
      - platform: time
        at: "23:00:00"
    condition:
      - condition: state
        entity_id: sensor.screenpilot_tv_status
        state: "on"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.screenpilot_tv
```

### 3. Show Dashboard in Morning

```yaml
automation:
  - alias: "ScreenPilot Morning Dashboard"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.screenpilot_tv
      - delay: "00:00:05"
      - service: rest_command.screenpilot_set_url
        data:
          host: "YOUR_SCREENPILOT_IP"
          token: "YOUR_API_TOKEN"
          url: "http://YOUR_HA_IP:8123/lovelace/dashboard"
```

## 📱 Dashboard Examples

Create a custom card for controlling ScreenPilot:

```yaml
type: vertical-stack
cards:
  - type: markdown
    content: |
      ## ScreenPilot Control
      **Status:** {{ states('sensor.screenpilot_status') }}
      **Current URL:** {{ states('sensor.screenpilot_display_url') }}
      
  - type: horizontal-stack
    cards:
      - type: button
        name: "TV Power"
        icon: mdi:television
        entity: switch.screenpilot_tv
        tap_action:
          action: toggle
          
      - type: button
        name: "Refresh"
        icon: mdi:refresh
        tap_action:
          action: call-service
          service: rest_command.screenpilot_reload_page
          service_data:
            host: "YOUR_SCREENPILOT_IP"
            token: "YOUR_API_TOKEN"
            
      - type: button
        name: "Restart"
        icon: mdi:restart
        tap_action:
          action: call-service
          service: rest_command.screenpilot_restart_browser
          service_data:
            host: "YOUR_SCREENPILOT_IP"
            token: "YOUR_API_TOKEN"
            
  - type: entities
    entities:
      - entity: input_select.screenpilot_quick_urls
      - entity: input_text.screenpilot_custom_url
      
  - type: picture-entity
    entity: camera.screenpilot_display
    camera_view: live
    
  - type: entities
    title: "System Info"
    entities:
      - entity: sensor.screenpilot_cpu_usage
        name: "CPU"
      - entity: sensor.screenpilot_memory_usage
        name: "Memory"
      - entity: sensor.screenpilot_disk_usage
        name: "Disk"
      - entity: sensor.screenpilot_uptime
        name: "Uptime"
```

## 🔌 Services Available

The custom integration provides these services:

- `screenpilot.set_url` - Navigate to URL
- `screenpilot.reload_page` - Refresh current page
- `screenpilot.restart_browser` - Restart browser
- `screenpilot.clear_browser_data` - Clear all browser data
- `screenpilot.set_session_mode` - Change session persistence
- `screenpilot.send_cec_command` - Send TV commands
- `screenpilot.control_service` - Control system services

### Navigate to URL Script

```yaml
script:
  screenpilot_navigate:
    alias: "Navigate ScreenPilot"
    fields:
      url:
        description: "URL to navigate to"
        example: "https://example.com"
    sequence:
      - service: rest_command.screenpilot_set_url
        data:
          host: "YOUR_SCREENPILOT_IP"
          token: "YOUR_API_TOKEN"
          url: "{{ url }}"
```

### CEC Control Script

```yaml
script:
  screenpilot_cec:
    alias: "Send CEC Command"
    fields:
      command:
        description: "CEC command to send"
        example: "volume_up"
    sequence:
      - service: rest_command.screenpilot_cec_command
        data:
          host: "YOUR_SCREENPILOT_IP"
          token: "YOUR_API_TOKEN"
          command: "{{ command }}"
```

## 🧪 Troubleshooting

1. Replace `YOUR_SCREENPILOT_IP` with your ScreenPilot IP address
   - Production: Use IP only (e.g., `192.168.1.100`)
   - Development: Use IP:8000 (e.g., `192.168.1.100:8000`)
2. Replace `YOUR_API_TOKEN` with your API token
3. Restart Home Assistant
4. Check Developer Tools > States for new entities
5. Test commands in Developer Tools > Services

### Connection Issues
- Test with the provided script: `./scripts/test_api.sh YOUR_IP TOKEN`
- Check firewall rules allow port 80 (production) or 8000 (dev)
- Verify API token matches

### Entity Not Updating
- Check Home Assistant logs
- Reload the integration
- Verify ScreenPilot services are running

### Common Issues
- **Wrong port**: Production uses 80, development uses 8000
- **API token mismatch**: Check `/etc/screenpilot/screenpilot.conf` on Pi
- **Network isolation**: Ensure HA can reach ScreenPilot's network

## 📚 Directory Structure

```
home_assistant/
├── custom_components/screenpilot/  # Custom integration (recommended)
├── examples/                       # Example configurations
│   ├── configuration_manual.yaml   # Single device manual config
│   ├── configuration_multi.yaml    # Multi-device manual config
│   ├── automations.yaml           # Automation examples
│   └── lovelace-card.yaml         # Dashboard examples
├── scripts/                       # Utility scripts
│   └── test_api.sh               # API testing script
└── README.md                      # This file
```

## 🚀 Next Steps

1. **Install the custom integration** using the steps above
2. **Add your ScreenPilot devices** through the UI
3. **Import example automations** from `examples/automations.yaml`
4. **Create dashboards** using `examples/lovelace-card.yaml` as a template
5. **Test the API** with `scripts/test_api.sh`

## 💡 Advanced Use Cases

- **Multi-room displays**: Control all kiosks from one dashboard
- **Scheduled content**: Rotate URLs based on time/events
- **Presence detection**: Turn on/off displays based on room occupancy
- **Alert displays**: Show critical information during emergencies
- **Energy saving**: Power off displays during inactive hours

## 🆘 Support

- **ScreenPilot Issues**: [Main ScreenPilot repository](https://github.com/kurtislanderson/ScreenPilot)
- **Integration Issues**: [Create an issue here](https://github.com/kurtislanderson/screenpilot-homeassistant/issues)
- **Home Assistant Community**: [Community Forum](https://community.home-assistant.io/)

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Thanks to the Home Assistant community
- Built for use with [ScreenPilot](https://github.com/kurtislanderson/ScreenPilot)