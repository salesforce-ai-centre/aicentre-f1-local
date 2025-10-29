# Architecture Overview

## System Components

```
┌─────────────────────────────────────────────────────────┐
│              Mac Host (172.18.159.209)                  │
│                                                         │
│  ┌─────────────┐      ┌──────────────────────────┐    │
│  │ Flask       │      │ UDP Receivers (x2)       │    │
│  │ (port 8080) │      │ - Rig 1: port 20777      │    │
│  │             │◄─────┤ - Rig 2: port 20778      │    │
│  │ /dual route │      │                          │    │
│  │ SSE stream  │      │ Decode F1 UDP → JSON     │    │
│  └──────┬──────┘      └────────▲─────────────────┘    │
│         │                      │                       │
└─────────┼──────────────────────┼───────────────────────┘
          │                      │
          │ Network              │ UDP
          │                      │
    ┌─────▼──────────┐    ┌─────┴───────────┐
    │ Sim 1 PC       │    │ Sim 2 PC        │
    │ (192.168.8.22) │    │ (192.168.8.21)  │
    │                │    │                 │
    │ F1 Game        │    │ F1 Game         │
    │ Chrome Browser │    │ Chrome Browser  │
    └────────────────┘    └─────────────────┘
```

## Data Flow

1. **F1 Games** send UDP telemetry at 60Hz
2. **UDP Receivers** decode binary packets and POST JSON to Flask
3. **Flask** broadcasts via SSE to all connected browsers
4. **Dashboard** updates in real-time (<10ms latency)

## Code Structure

```
src/
├── app.py                  # Flask server + routes
├── receiver.py             # UDP decoder
├── models/                 # Data models
├── repositories/           # Database access
└── services/               # Business logic

templates/
└── dual_rig_dashboard.html # Main UI

static/
├── css/                    # Styling
└── js/                     # (inline in HTML)
```

## Key Design Patterns

- **Repository Pattern**: Database abstraction
- **Service Layer**: Business logic separation
- **SSE**: Real-time streaming
- **Separate Processes**: One receiver per rig (no shared state)

## Configuration

Environment variables in `config/.env`:
```bash
# Optional Salesforce integration
DATACLOUD_ENABLED=false

# Sim SSH (for window control)
SIM1_SSH_HOST=sim1admin@192.168.8.22
SIM2_SSH_HOST=sim2admin@192.168.8.21
```

## Database

SQLite with Salesforce-compatible schema:
- `Session__c` - Driver sessions
- `LapRecord__c` - Lap times

## Performance

- SSE latency: <10ms
- Memory: ~100MB total
- CPU: <15% on M-series Mac
- Telemetry rate: 60Hz per rig
