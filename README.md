# F1 Telemetry Dashboard

Real-time dual-rig F1 telemetry dashboard for F1 25/24 game. Shows two simulators side-by-side with live track map.

![Dashboard Status](https://img.shields.io/badge/status-production-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)

## Quick Start

### Mac/Linux
```bash
# Install dependencies
pip install -r config/requirements.txt

# Start system
./scripts/start_mac.sh

# Open dashboard
open http://localhost:8080/dual
```

### Windows (PowerShell)
```powershell
# Install dependencies
pip install -r config/requirements.txt

# Start system
.\scripts\start_windows.ps1

# Open dashboard
start http://localhost:8080/dual
```

### Windows (Command Prompt)
```batch
REM Install dependencies
pip install -r config\requirements.txt

REM Start system
scripts\start_windows.bat

REM Open dashboard
start http://localhost:8080/dual
```

## Features

- ✅ **Dual Dashboard** - Two simulators side-by-side
- ✅ **Live Track Map** - Real-time car positions
- ✅ **60Hz Telemetry** - Speed, gear, RPM, inputs, tyres
- ✅ **Session Management** - Driver registration via QR code
- ✅ **F1 Calendar** - Auto-selects current race
- ⚙️ **Data Cloud** - Optional Salesforce streaming

## System Requirements

- **Host PC**: Windows 10/11 or Mac (M1/M2/Intel) with Python 3.11+
- **Sim PCs**: Windows or Linux running F1 25 or F1 24
- **Network**: All PCs on same network

## Configuration

**F1 Game Settings:**
- Telemetry → UDP: ON
- Sim 1: IP `172.18.159.209`, Port `20777`
- Sim 2: IP `172.18.159.209`, Port `20778`

**Environment Variables** (optional):
```bash
cp config/.env.example config/.env
nano config/.env
```

## Project Structure

```
├── src/                    # Python application
│   ├── app.py             # Flask server
│   ├── receiver.py        # UDP decoder
│   └── ...
├── templates/             # HTML pages
├── static/                # CSS/JS/images
├── config/                # Configuration
├── scripts/               # Utility scripts
└── docs/                  # Documentation
```

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Step-by-step setup guide
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture
- **[docs/README.md](docs/README.md)** - Complete documentation
- **[CLAUDE.md](CLAUDE.md)** - AI assistant context

## Commands

### Mac/Linux
```bash
# Start all services
./scripts/start_mac.sh

# Stop all services
./scripts/stop_mac.sh

# View logs
tail -f logs/flask.log
```

### Windows (PowerShell)
```powershell
# Start all services
.\scripts\start_windows.ps1

# Stop all services
.\scripts\stop_windows.ps1

# View logs
Get-Content logs\flask.log -Wait
```

### Windows (Command Prompt)
```batch
# Start all services
scripts\start_windows.bat

# Stop all services
scripts\stop_windows.bat

# View logs
type logs\flask.log
```

## URLs

- **Dual Dashboard**: http://localhost:8080/dual
- **Attract Screen (Rig 1)**: http://localhost:8080/attract?rig=1
- **Attract Screen (Rig 2)**: http://localhost:8080/attract?rig=2
- **Welcome/Admin**: http://localhost:8080/

## Troubleshooting

**Port already in use:**

*Mac/Linux:*
```bash
./scripts/stop_mac.sh
# or
lsof -ti :20777 :20778 :8080 | xargs kill
```

*Windows (PowerShell):*
```powershell
.\scripts\stop_windows.ps1
```

**Receiver not connecting:**
- Check F1 game telemetry settings
- Verify IP address matches host machine
- Check firewall isn't blocking UDP ports

## Development

Built with:
- Flask 3.1.2
- Python 3.11+
- SQLite
- Server-Sent Events (SSE)
- F1 25/24 UDP protocol

## Team

Internal project for AI Centre F1 simulator experience.

## License

Internal use only.
