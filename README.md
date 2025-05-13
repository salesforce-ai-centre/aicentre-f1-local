# F1 Dashboard

A real-time Formula 1 telemetry dashboard that captures and displays live data from the F1 24 video game.

## Features

- Real-time display of speed, RPM, gear, and pedal inputs
- Tyre wear and brake temperature monitoring
- ERS and DRS status indicators
- Damage reporting
- Lap timing and position tracking
- Event notifications (completed laps, flags, etc.)
- **AI Race Engineer** that provides contextual coaching via Salesforce AI Models API

## Requirements

- F1 24 game with UDP telemetry enabled
- Python 3.x
- Web browser (Chrome, Firefox, etc.)

## Quick Start

### One-Command Setup

Run both the dashboard server and telemetry receiver with a single command:

```bash
python3 run_dashboard.py --driver "Jacob Berry" --track "Japan"
```

Your web browser will automatically open with the dashboard, and the system will be ready to receive telemetry from the F1 game.

### Command-line Options

```
usage: run_dashboard.py [-h] [--driver DRIVER] [--track TRACK] [--port PORT] [--no-browser] [--debug]

Start F1 Dashboard components with a single command

options:
  -h, --help         show this help message and exit
  --driver DRIVER    Driver name to display on dashboard
  --track TRACK      Track name to display on dashboard
  --port PORT        Port for the web server (default: 5000)
  --no-browser       Don't automatically open web browser
  --debug            Enable debug mode for more verbose logging
```

## F1 Game Settings

1. In F1 24, navigate to Settings → Telemetry Settings
2. Enable UDP Telemetry
3. Set UDP Port to 20777 (default)
4. Set UDP Format to F1 2024
5. Set UDP Broadcast Mode according to your network setup

## Manual Setup (Component-by-Component)

If you prefer to start components individually:

### Dashboard Server

```bash
flask run --debug
```

Or for production:

```bash
python app.py
```

### Telemetry Receiver

```bash
python receiver.py --url http://localhost:5000/data --driver "YourName" --track "Circuit"
```

## Architecture

- **app.py**: Flask web server that hosts the dashboard interface and broadcasts telemetry data
- **receiver.py**: Listens for UDP packets from the F1 game, processes the data, and sends it to the server
- **templates/index.html**: Main dashboard HTML structure
- **static/js/script.js**: JavaScript code for real-time dashboard updates
- **static/css/style.css**: Dashboard styling

## AI Race Engineer Setup

The dashboard includes an AI race engineer that provides contextual coaching using the Salesforce Models API with OpenAI's GPT-4o model (GPT-4 Omni) for advanced natural language understanding and instruction following.

### Configuration

1. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Configure your Salesforce Connected App and Models API credentials:

#### Salesforce Models API Setup

1. Configure a Connected App in your Salesforce org:
   - In Salesforce Setup, go to Apps → App Manager → New Connected App
   - Fill in the basic information:
     - Connected App Name: F1 Dashboard
     - API Name: F1_Dashboard
     - Contact Email: Your email

   - Enable OAuth Settings:
     - Check "Enable OAuth Settings"
     - Callback URL: http://localhost:5000/callback (not actually used, but required)
     - Selected OAuth Scopes: Add "Access and manage your data (api)" 

   - Save the Connected App

2. Add credentials to your `.env` file:
   ```
   SF_CLIENT_ID=your_client_id_here
   SF_CLIENT_SECRET=your_client_secret_here
   ```

3. For the Models API, ensure you have Einstein Platform access configured in your Salesforce org.

### How it Works

The AI race engineer:
- Analyzes telemetry data in real-time
- Detects important events (completed laps, damage, high tire wear, etc.)
- Sends prompts to the Salesforce Models API with context about the race situation
- Receives AI-generated coaching messages customized to your driving
- Delivers these messages through team radio sound effects and text-to-speech

Messages are triggered by:
- Completing a lap (with performance feedback)
- Sustaining significant damage
- High tire wear detection
- DRS availability
- Race strategy considerations based on position
- And more!