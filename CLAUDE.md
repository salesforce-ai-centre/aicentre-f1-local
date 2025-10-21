# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a real-time F1 telemetry dashboard that captures UDP data from the F1 25 or F1 24 video game, visualizes it in a web interface, and optionally streams data to Salesforce Data Cloud. The system consists of three main components that work together:

1. **UDP Receiver** (`src/receiver.py`) - Listens for F1 game telemetry on port 20777, decodes binary packets, and forwards JSON to the Flask server
2. **Flask Web Server** (`src/app.py`) - Hosts the dashboard UI and broadcasts telemetry via Server-Sent Events (SSE)
3. **Web Dashboard** (`templates/index.html` + `static/`) - Real-time visualization using Chart.js and custom JavaScript

## Commands

### Development

```bash
# Start the complete system (recommended for development and normal use)
python3 scripts/run_dashboard.py --driver "Your Name" --datacloud

# Start components separately (for debugging)
python3 src/app.py                    # Start Flask server only
python3 src/receiver.py --url http://localhost:8080/data --driver "Your Name"  # Start receiver only

# Install dependencies
pip install -r config/requirements.txt
```

### Testing

```bash
# Run performance tests
python3 scripts/run_performance_test.py

# Simulate F1 telemetry load
python3 tests/load_test_simulator.py --stress --duration 300

# Monitor system performance
python3 tests/performance_monitor.py --duration 300 --output perf_results.jsonl

# Test Data Cloud integration standalone
python3 tests/test_datacloud_standalone.py
```

## Architecture

### Data Flow

1. **F1 Game** → UDP packets (port 20777) → **receiver.py**
2. **receiver.py** → HTTP POST `/data` → **app.py**
3. **app.py** → SSE stream `/stream` → **Web Browser**
4. **app.py** → (optional) Data Cloud JWT Auth → **Salesforce Data Cloud**

### Key Components

**receiver.py** (~27k tokens, read with offset/limit if needed):
- Decodes F1 25/24 UDP binary protocol (see `docs/UDPSPEC.md` for F1 24, `docs/F1 25 Telemetry Output Structures.txt` for F1 25)
- Maintains state for `m_header`, `m_lapData`, `m_carStatus`, `m_carDamage`, `m_motion`, `m_session`
- Implements auto-track detection by mapping `trackId` to human-readable names
- Batches data and sends to Flask at ~10ms intervals (`--send-interval`)
- Performance metrics logged every 10 seconds (CPU, memory, thread count)

**app.py**:
- Uses thread-safe `message_queue` (queue.Queue) for SSE broadcasting
- Stores `latest_data` with `data_lock` for new client initialization
- Event detection logic compares current vs previous data (lap completion, damage, tire wear)
- AI Race Engineer (currently disabled: `AI_ENABLED = False`) using Salesforce Models API with GPT-4o
- Async AI message generation via `concurrent.futures.ThreadPoolExecutor` to avoid blocking telemetry
- Data Cloud integration via `datacloud_integration.py` (JWT Bearer Flow authentication)

**datacloud_integration.py**:
- `DataCloudClient` handles JWT authentication with RSA key pairs
- Transforms telemetry to match Data Cloud schema (see `docs/f1-telemetry-datacloud-schema.yaml`)
- Batches records for efficient transmission (default: 10 records per batch, 2s timeout)
- Supports multiple stream endpoints: telemetry, events, sessions, participants, motion
- Implements token exchange for Data Cloud-specific JWT tokens

### Critical Implementation Details

**SSE Performance**: The `/stream` endpoint uses ultra-short timeout (0.001s) optimized for local operation. This wouldn't scale to multiple clients but provides <10ms latency for single-user dashboard.

**UDP Binary Protocol**: F1 25/24 uses a complex binary format. All packet parsing happens in `receiver.py`. The packet header contains `m_packetFormat` (2025 for F1 25, 2024 for F1 24), `m_packetVersion`, `m_packetId` which determines packet type (0=Motion, 2=Lap Data, 7=Car Status, 10=Car Damage, 15=Lap Positions [F1 25 only], etc.).

**Track Auto-Detection**: `receiver.py` maintains a track ID → name mapping for all F1 25/24 circuits. When track data arrives, it automatically updates the payload. Disable with `--no-auto-track` flag.

**JWT Authentication**: Data Cloud requires RSA-signed JWT tokens. Private key at `SF_PRIVATE_KEY_PATH`, public key uploaded to Salesforce Connected App. Token exchange flow: Salesforce token → Data Cloud-specific token.

**Event Detection Logic**: In `app.py`, events are detected by comparing `data` vs `latest_data`:
- Lap completion: `data.get("lapCompleted") and not latest_data.get("lapCompleted")`
- Damage: Check each damage component for >15% increase
- Tire wear: Check if any tire exceeds 70% wear threshold
- Always update `latest_data = data.copy()` AFTER comparisons

## Configuration

### Environment Variables

Required for Data Cloud integration (config/.env):
```
DATACLOUD_ENABLED=true
SALESFORCE_DOMAIN=your-org.my.salesforce.com
SF_CLIENT_ID=your_connected_app_client_id
SF_PRIVATE_KEY_PATH=./private.key
SF_USERNAME=your-salesforce-username@domain.com

# For AI Race Engineer (currently disabled)
SF_CLIENT_SECRET=your_client_secret

# Data Cloud stream endpoints
DC_TELEMETRY_ENDPOINT=https://subdomain.c360a.salesforce.com/api/v1/ingest/sources/SOURCE/STREAM
DC_EVENTS_ENDPOINT=https://subdomain.c360a.salesforce.com/api/v1/ingest/sources/SOURCE/EVENTS
```

### F1 Game Settings

In F1 25 or F1 24, enable telemetry:
- Settings → Telemetry Settings
- UDP Telemetry: ON
- UDP Port: 20777 (default)
- UDP Format: F1 2025 (for F1 25 game) or F1 2024 (for F1 24 game)
- UDP Broadcast Mode: (configure for your network)

## Development Guidelines

### Adding New Telemetry Fields

1. Decode the field in `receiver.py` from the appropriate packet type
2. Add to payload in `_prepare_payload()` method
3. Update Data Cloud schema in `datacloud_integration.py` (`_transform_telemetry_record()`)
4. Add visualization in `static/js/script.js` and `templates/index.html`

### Adding Event Detection

Add logic in `app.py` `/data` endpoint:
1. Compare `data` vs `latest_data` to detect state changes
2. Create event object: `{"message": "...", "type": "..."}`
3. Set `data["event"] = event_to_send`
4. Optionally trigger AI coach message with `generate_ai_coach_message_async()`

### Performance Considerations

- **UDP Receiver**: Target <5% CPU usage. Increase `--send-interval` if CPU is high
- **SSE Broadcasting**: Queue size should remain <100 items. If growing, clients aren't consuming fast enough
- **Memory Leaks**: Monitor with `tests/performance_monitor.py`. Expected usage: <150MB total
- **Data Cloud Rate Limits**: Batch size is 10 records. Adjust `batch_size` and `batch_timeout` in `DataCloudClient` if hitting rate limits

### AI Race Engineer (Currently Disabled)

The AI system uses Salesforce Models API with GPT-4o. To enable:
1. Set `AI_ENABLED = True` in `app.py`
2. Configure `SF_CLIENT_ID` and `SF_CLIENT_SECRET` in .env
3. AI messages are generated asynchronously via thread pool to avoid blocking telemetry
4. Prompts are in `create_prompt_for_event()` - tune these for better responses
5. Message types: lap_completed, damage_detected, tire_wear, tire_strategy, fuel_strategy, performance_coaching, strategy, drs_available

## File Organization

```
├── src/                       # Main application code
│   ├── app.py                 # Flask server + SSE + event detection
│   ├── receiver.py            # UDP telemetry receiver + F1 protocol decoder
│   └── datacloud_integration.py  # Salesforce Data Cloud client
├── scripts/                   # Utility scripts
│   ├── run_dashboard.py       # Launcher script (starts both components)
│   ├── run_performance_test.py
│   └── setup.sh
├── tests/                     # Testing and performance tools
│   ├── load_test_simulator.py
│   ├── performance_monitor.py
│   └── test_*.py
├── templates/                 # HTML templates
│   └── index.html             # Main dashboard UI
├── static/                    # Frontend assets
│   ├── js/script.js           # Dashboard logic + Chart.js
│   ├── css/style.css
│   └── sounds/                # Team radio sound effects
├── config/                    # Configuration files
│   ├── .env.example
│   ├── requirements.txt
│   ├── Procfile
│   └── f1-telemetry-datacloud-schema.yaml
└── docs/                      # Documentation
    ├── README.md              # Complete setup guide
    ├── UDPSPEC.md             # F1 24 UDP protocol spec
    ├── F1 25 Telemetry Output Structures.txt  # F1 25 UDP protocol structures
    ├── Data Output from F1 25 v3.pdf         # F1 25 UDP protocol documentation
    ├── PERFORMANCE_TESTING.md
    └── models.md              # Salesforce Models API docs
```

## Troubleshooting

**Port 20777 in use**: Run `lsof -ti :20777 | xargs kill` or use `run_dashboard.py` which auto-kills conflicting processes

**401 Unauthorized from Data Cloud**: JWT token likely expired or invalid. Check:
- Private key file exists at `SF_PRIVATE_KEY_PATH`
- Public key uploaded to Connected App
- Connected App has "cdp_api" scope
- Token exchange is succeeding (check logs for "Data Cloud token exchange successful")

**High CPU usage**: Reduce packet send frequency with `--send-interval 0.02` (20ms instead of 10ms)

**SSE connection drops**: Check browser console for errors. SSE requires persistent HTTP connection. Some proxies/firewalls may terminate long-lived connections.

**Track name not auto-detecting**: Ensure F1 game is sending Session packet (packet ID 1). Check receiver logs for "Auto-detected track". Use `--no-auto-track` to disable.

## Documentation References

- F1 UDP Protocol: `docs/UDPSPEC.md` and `docs/F1 25 Telemetry Output Structures.txt`
- Data Cloud Schema: `config/f1-telemetry-datacloud-schema.yaml`
- Performance Testing: `docs/PERFORMANCE_TESTING.md`
- Salesforce Models API: `docs/models.md`
