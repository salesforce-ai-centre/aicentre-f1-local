# F1 Dual-Rig Telemetry Dashboard

> Real-time telemetry visualization for two F1 simulators with live track mapping

![Dashboard Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## Overview

A production-ready dual-rig F1 telemetry dashboard designed for 55-inch 4K TV displays. Captures UDP data from two F1 25/24 game instances simultaneously, visualizes telemetry in real-time, and displays both drivers on a live track map for easy side-by-side comparison.

### Key Features

- ✅ **Dual-Rig Support**: Monitor two simulators simultaneously
- ✅ **Real-Time Track Map**: Live 2D visualization with both drivers' positions
- ✅ **3-Column Layout**: Optimized for 4K TV comparison (Sim 1 | Map | Sim 2)
- ✅ **Comprehensive Telemetry**: Speed, RPM, Gear, Steering, Tires, Damage
- ✅ **WebSocket Streaming**: Sub-10ms latency updates
- ✅ **Marshal Zone Visualization**: Track flags in real-time
- ✅ **Session State Management**: Auto-detects session start/end
- ✅ **Data Cloud Integration**: Optional Salesforce Data Cloud streaming

## Quick Start

### Prerequisites

- Python 3.8+
- F1 25 or F1 24 game
- Two sim PCs on same network
- 4K display recommended

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### Running

```bash
# Start dual-rig dashboard
python3 scripts/run_dual_dashboard.py

# Open http://localhost:8080
# Press F11 for fullscreen on TV
```

## Project Structure

```
aicentre-f1-local/
├── src/                   # Source code
│   ├── app_dual_rig.py   # Main Flask app (ACTIVE)
│   ├── receiver_multi.py # UDP receiver
│   └── telemetry_gateway.py
├── templates/             # HTML templates
│   └── dual_rig_dashboard.html  (ACTIVE)
├── static/                # Frontend assets
│   ├── js/
│   │   ├── dual-rig-dashboard.js (ACTIVE)
│   │   └── track-map.js         (ACTIVE)
│   ├── css/
│   │   └── dual-rig-style.css   (ACTIVE)
│   └── tracks/            # 30 F1 circuit files
├── scripts/               # Utilities
│   └── run_dual_dashboard.py (MAIN LAUNCHER)
├── docs/                  # Documentation
│   ├── setup/
│   ├── architecture/
│   └── development/
└── tests/                 # Test suite
```

## Documentation

- **[Setup Guide](docs/setup/DUAL_RIG_SETUP.md)** - Complete installation
- **[Architecture](docs/architecture/DUAL_RIG_ARCHITECTURE.md)** - System design
- **[Feature Roadmap](docs/development/FEATURE_ANALYSIS.md)** - Future features

## Configuration

Edit `.env`:

```bash
RIG_A_PORT=20777
RIG_A_DRIVER="Jacob Berry"
RIG_B_PORT=20778
RIG_B_DRIVER="Chris Webb"
```

Configure F1 Game:
```
Settings → Telemetry → UDP ON
Port: 20777 (Sim 1) / 20778 (Sim 2)
Host IP: Your dashboard PC IP
```

## Troubleshooting

**No data from sims?**
```bash
# Test reception
python3 scripts/test_dual_receiver.py

# Check firewall allows UDP ports 20777/20778
```

**Track map not loading?**
- Verify `static/tracks/` directory exists
- Check browser console for errors
- Ensure session packet contains valid trackId

## Contributing

Contributions welcome! Fork, create feature branch, and submit PR.

## License

MIT License

## Support

- Issues: GitHub Issues
- Discussions: GitHub Discussions

---

**Built with ❤️ for sim racing**
