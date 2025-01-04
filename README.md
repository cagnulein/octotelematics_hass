# OCTO Telematics Integration for Home Assistant

This custom integration allows you to monitor your vehicle statistics from OCTO Telematics in Home Assistant.

![OCTO Telematics Screenshot](/docs/screenshot.png)

## Features

- Displays total kilometers driven
- Shows last update date
- Automatically updates every 10 minutes (configurable)

## Installation

### HACS (Recommended)
1. Add this repository to HACS as a custom repository:
    - Click on HACS in the sidebar
    - Click on Integrations
    - Click the three dots in the top right corner
    - Click "Custom repositories"
    - Add the URL of this repository
    - Category: Integration
2. Click Install
3. Restart Home Assistant

### Manual Installation
1. Download the latest release
2. Copy the `custom_components/octotelematics` folder to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

### Through UI (Recommended)
1. Go to Settings -> Devices & Services
2. Click "+" to add a new integration
3. Search for "OCTO Telematics"
4. Enter your credentials

### Through YAML
Add to your `configuration.yaml`:

```yaml
octotelematics:
  username: YOUR_USERNAME
  password: YOUR_PASSWORD
  scan_interval: 1440  # Optional, in minutes
```

## Sensors

The integration creates the following sensor:

- `sensor.octo_total_kilometers`: Shows total kilometers driven
  - State: Total kilometers value
  - Attributes:
    - `last_update`: Date of last update (YYYY-MM-DD format)
    - Unit of measurement: km

## Debug Mode

To enable debug logs, add this to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.octotelematics: debug
```

## Support

For bugs and feature requests, please open an issue on GitHub.

## Disclaimer

This integration is not affiliated with or endorsed by OCTO Telematics.

## License

[MIT License](LICENSE)