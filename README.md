# F1 Dashboard

A real-time Formula 1 telemetry dashboard that captures and displays live data from the F1 24 video game.

## Features

- Real-time display of speed, RPM, gear, and pedal inputs
- Tyre wear and brake temperature monitoring
- ERS and DRS status indicators
- Damage reporting
- Lap timing and position tracking
- Event notifications (completed laps, flags, etc.)
- **Automatic track detection** from F1 game data
- **AI Race Engineer** that provides contextual coaching via Salesforce AI Models API
- **Salesforce Data Cloud integration** for telemetry streaming

## Quick Start

### One-Command Setup

Run both the dashboard server and telemetry receiver with a single command:

```bash
python3 scripts/run_dashboard.py --driver "Your Name" --datacloud
```

Your web browser will automatically open with the dashboard, and the system will be ready to receive telemetry from the F1 game.

### Requirements

- F1 24 game with UDP telemetry enabled
- Python 3.x
- Web browser (Chrome, Firefox, etc.)

## Installation

1. Install dependencies:
   ```bash
   pip install -r config/requirements.txt
   ```

2. Configure environment (optional, for Data Cloud/AI features):
   ```bash
   cp config/.env.example .env
   # Edit .env with your Salesforce credentials
   ```

3. Configure F1 game:
   - Navigate to Settings → Telemetry Settings
   - Enable UDP Telemetry
   - Set UDP Port to 20777 (default)
   - Set UDP Format to F1 2024

## Project Structure

```
├── config/              # Configuration files (.env, requirements.txt, etc.)
├── docs/                # Documentation
├── scripts/             # Utility scripts (setup, run_dashboard, performance testing)
├── src/                 # Main application code
│   ├── app.py          # Flask web server
│   ├── receiver.py     # UDP telemetry receiver
│   └── datacloud_integration.py  # Salesforce Data Cloud integration
├── static/              # Frontend assets (CSS, JS, images)
├── templates/           # HTML templates
├── tests/               # Test files and performance monitoring
└── logs/                # Runtime logs
```

## Documentation

- [Complete Setup Guide](docs/README.md) - Detailed setup instructions including Salesforce integration
- [Performance Testing](docs/PERFORMANCE_TESTING.md) - Load testing and performance monitoring
- [F1 UDP Specification](docs/UDPSPEC.md) - F1 24 telemetry data format
- [AI Models Documentation](docs/models.md) - Salesforce Models API details

## Usage Options

### Command-line Arguments

```
usage: run_dashboard.py [-h] [--driver DRIVER] [--track TRACK] [--no-auto-track]
                        [--port PORT] [--no-browser] [--debug] [--datacloud]

options:
  --driver DRIVER      Driver name to display on dashboard
  --track TRACK        Track name (auto-detected by default)
  --no-auto-track      Disable automatic track detection
  --port PORT          Web server port (default: 8080)
  --no-browser         Don't automatically open browser
  --debug              Enable debug logging
  --datacloud          Enable Salesforce Data Cloud streaming
```

## Contributing

This is a personal project for F1 telemetry visualization and AI-powered race coaching.

## License

[Add your license here]
