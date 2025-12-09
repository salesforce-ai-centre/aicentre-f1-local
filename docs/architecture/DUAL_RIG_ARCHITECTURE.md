# Dual-Rig F1 Telemetry Architecture

## Overview
Transform the existing single-rig dashboard into a professional dual-rig telemetry gateway that ingests UDP from two F1 25 sim PCs, displays real-time data on a unified dashboard, and streams normalized telemetry to Salesforce Data Cloud.

**Current State:** Single receiver → Flask → SSE → Browser
**Target State:** Dual receivers → Telemetry Gateway → WebSocket → Multi-rig Dashboard → Data Cloud

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SIM RIG A (192.168.1.10)                       │
│  F1 25 → UDP:20777 ──────────────────────────────────┐                  │
└──────────────────────────────────────────────────────┼──────────────────┘
                                                        │
┌─────────────────────────────────────────────────────┼──────────────────┐
│                           SIM RIG B (192.168.1.11)   │                  │
│  F1 25 → UDP:20778 ──────────────────────────────────┤                  │
└──────────────────────────────────────────────────────┼──────────────────┘
                                                        │
                                                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    HOST PC (192.168.1.100) - Telemetry Gateway          │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │                    UDP Ingestor Service                       │      │
│  │  ┌────────────────┐              ┌────────────────┐          │      │
│  │  │ Receiver A     │              │ Receiver B     │          │      │
│  │  │ Port: 20777    │              │ Port: 20778    │          │      │
│  │  │ SimID: RIG_A   │              │ SimID: RIG_B   │          │      │
│  │  └────────┬───────┘              └────────┬───────┘          │      │
│  │           └──────────────┬────────────────┘                  │      │
│  │                          ▼                                    │      │
│  │              ┌───────────────────────┐                        │      │
│  │              │  Packet Router        │                        │      │
│  │              │  (sessionUID-based)   │                        │      │
│  │              └───────────┬───────────┘                        │      │
│  └──────────────────────────┼──────────────────────────────────┘      │
│                              ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │              Session Registry & Normalizer                    │      │
│  │  • Track session metadata (sessionUID, track, drivers)        │      │
│  │  • Join participant names to vehicle indices                 │      │
│  │  • Normalize packets to canonical event model                │      │
│  │  • Handle privacy flags (restricted telemetry)               │      │
│  └──────────────────────────┬───────────────────────────────────┘      │
│                              ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │                  Event Distribution Layer                     │      │
│  │                                                               │      │
│  │  ┌────────────────┐    ┌──────────────┐   ┌──────────────┐  │      │
│  │  │ WebSocket Hub  │    │ Local Buffer │   │ DC Uploader  │  │      │
│  │  │ (10-20 Hz)     │    │ (SQLite)     │   │ (250-500ms)  │  │      │
│  │  └────────┬───────┘    └──────────────┘   └──────┬───────┘  │      │
│  └───────────┼────────────────────────────────────────┼──────────┘      │
│              │                                         │                 │
│              ▼                                         ▼                 │
│  ┌─────────────────────────┐          ┌──────────────────────────────┐ │
│  │  Flask Web Server       │          │  Data Cloud API Client       │ │
│  │  • Serve dashboard      │          │  • JWT authentication        │ │
│  │  • WebSocket endpoint   │          │  • Token exchange            │ │
│  │  • Health/metrics API   │          │  • Batch uploader (200KB)    │ │
│  └─────────────────────────┘          │  • 429 backoff & retry       │ │
│                                        └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │   Browser Dashboard   │
                  │   • Split-screen view │
                  │   • Real-time charts  │
                  │   • Event timeline    │
                  └───────────────────────┘
```

---

## Implementation Plan

### Phase 1: Multi-Receiver Core (Week 1)

#### 1.1 Create Multi-Receiver Architecture

**New file:** `src/telemetry_gateway.py`

```python
"""
Multi-rig telemetry gateway
Manages multiple UDP receivers and routes packets to processors
"""

import asyncio
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from queue import Queue
import threading

from config import NUM_CARS
from receiver import F1TelemetryReceiver

logger = logging.getLogger(__name__)


@dataclass
class RigConfig:
    """Configuration for a single sim rig"""
    rig_id: str  # e.g., "RIG_A", "RIG_B"
    udp_port: int
    driver_name: str
    device_id: str  # For Data Cloud foreign key
    individual_id: Optional[str] = None  # Optional unified individual ID


class TelemetryGateway:
    """
    Manages multiple F1 telemetry receivers and routes their data
    """

    def __init__(self, rigs: list[RigConfig], event_queue: Queue):
        self.rigs = rigs
        self.event_queue = event_queue
        self.receivers = {}
        self.active_sessions = {}  # sessionUID -> rig_id mapping
        self.running = False

    def start(self):
        """Start all receivers in separate threads"""
        logger.info(f"Starting telemetry gateway with {len(self.rigs)} rigs")
        self.running = True

        for rig in self.rigs:
            logger.info(f"Starting receiver for {rig.rig_id} on port {rig.udp_port}")
            receiver = F1TelemetryReceiver(
                rig_id=rig.rig_id,
                port=rig.udp_port,
                driver_name=rig.driver_name,
                event_callback=self._on_packet_received
            )

            thread = threading.Thread(
                target=receiver.run,
                name=f"Receiver-{rig.rig_id}",
                daemon=True
            )
            thread.start()

            self.receivers[rig.rig_id] = {
                'receiver': receiver,
                'thread': thread,
                'config': rig
            }

    def _on_packet_received(self, rig_id: str, packet_data: dict):
        """
        Callback when a receiver processes a packet
        Enriches with rig metadata and routes to event queue
        """
        # Enrich packet with rig identification
        enriched_packet = {
            **packet_data,
            'rig_id': rig_id,
            'source_type': 'f1_25',
            'timestamp_gateway': time.time()
        }

        # Track active sessions
        session_uid = packet_data.get('sessionUID')
        if session_uid and session_uid not in self.active_sessions:
            self.active_sessions[session_uid] = rig_id
            logger.info(f"New session {session_uid} started on {rig_id}")

        # Route to event queue for distribution
        self.event_queue.put(enriched_packet)

    def get_status(self) -> dict:
        """Get status of all receivers"""
        status = {
            'running': self.running,
            'active_sessions': len(self.active_sessions),
            'rigs': {}
        }

        for rig_id, rig_data in self.receivers.items():
            receiver = rig_data['receiver']
            status['rigs'][rig_id] = {
                'port': rig_data['config'].udp_port,
                'driver': rig_data['config'].driver_name,
                'packets_received': receiver.get_packet_count(),
                'last_packet_time': receiver.get_last_packet_time(),
                'active': receiver.is_active()
            }

        return status
```

#### 1.2 Update Receiver for Multi-Instance Support

**Modify:** `src/receiver.py`

Add callback support and rig identification:

```python
class F1TelemetryReceiver:
    def __init__(self, rig_id: str, port: int, driver_name: str,
                 event_callback: callable):
        self.rig_id = rig_id
        self.port = port
        self.driver_name = driver_name
        self.event_callback = event_callback
        self.packet_count = 0
        self.last_packet_time = None

    def _on_packet_decoded(self, packet_type: str, data: dict):
        """Called when a packet is successfully decoded"""
        self.packet_count += 1
        self.last_packet_time = time.time()

        # Invoke callback with rig context
        if self.event_callback:
            self.event_callback(self.rig_id, data)
```

### Phase 2: Event Distribution & WebSocket (Week 2)

#### 2.1 WebSocket Event Publisher

**New file:** `src/websocket_publisher.py`

```python
"""
WebSocket publisher for real-time dashboard updates
Uses Flask-SocketIO for WebSocket support
"""

from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
import logging
from queue import Queue, Empty
import threading
import time

logger = logging.getLogger(__name__)


class WebSocketPublisher:
    """
    Publishes telemetry events via WebSocket
    Supports per-rig subscriptions and aggregated views
    """

    def __init__(self, socketio: SocketIO, event_queue: Queue):
        self.socketio = socketio
        self.event_queue = event_queue
        self.running = False
        self.publish_rate_hz = 20  # 20 updates per second
        self.last_state = {}  # rig_id -> last published state

        # Register SocketIO event handlers
        self._register_handlers()

    def _register_handlers(self):
        """Register WebSocket event handlers"""

        @self.socketio.on('connect')
        def handle_connect():
            logger.info(f"Client connected: {request.sid}")
            emit('connection_status', {'status': 'connected'})

        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info(f"Client disconnected: {request.sid}")

        @self.socketio.on('subscribe_rig')
        def handle_subscribe_rig(data):
            """Subscribe to specific rig updates"""
            rig_id = data.get('rig_id')
            if rig_id:
                join_room(rig_id)
                logger.info(f"Client {request.sid} subscribed to {rig_id}")

                # Send current state immediately
                if rig_id in self.last_state:
                    emit('telemetry_update', self.last_state[rig_id])

        @self.socketio.on('unsubscribe_rig')
        def handle_unsubscribe_rig(data):
            """Unsubscribe from rig updates"""
            rig_id = data.get('rig_id')
            if rig_id:
                leave_room(rig_id)
                logger.info(f"Client {request.sid} unsubscribed from {rig_id}")

    def start(self):
        """Start publishing thread"""
        self.running = True
        thread = threading.Thread(target=self._publish_loop, daemon=True)
        thread.start()
        logger.info("WebSocket publisher started")

    def _publish_loop(self):
        """Main publishing loop"""
        interval = 1.0 / self.publish_rate_hz

        while self.running:
            start_time = time.time()

            # Process queued events
            events_processed = 0
            try:
                while events_processed < 100:  # Batch limit per cycle
                    event = self.event_queue.get(timeout=0.001)
                    self._process_event(event)
                    events_processed += 1
            except Empty:
                pass

            # Maintain consistent rate
            elapsed = time.time() - start_time
            if elapsed < interval:
                time.sleep(interval - elapsed)

    def _process_event(self, event: dict):
        """Process and publish a single event"""
        rig_id = event.get('rig_id')
        if not rig_id:
            return

        # Update cached state
        self.last_state[rig_id] = event

        # Broadcast to subscribers in that rig's room
        self.socketio.emit(
            'telemetry_update',
            event,
            room=rig_id
        )

        # Also broadcast to 'all' room for aggregate view
        self.socketio.emit(
            'telemetry_update',
            event,
            room='all'
        )
```

#### 2.2 Update Flask App for WebSocket

**Modify:** `src/app.py`

```python
from flask_socketio import SocketIO
from websocket_publisher import WebSocketPublisher
from telemetry_gateway import TelemetryGateway, RigConfig
from queue import Queue

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Create event distribution queue
event_queue = Queue(maxsize=10000)

# Configure rigs
rigs = [
    RigConfig(
        rig_id="RIG_A",
        udp_port=20777,
        driver_name=os.environ.get("DRIVER_A_NAME", "Driver A"),
        device_id="SIM_A",
        individual_id=os.environ.get("DRIVER_A_INDIVIDUAL_ID")
    ),
    RigConfig(
        rig_id="RIG_B",
        udp_port=20778,
        driver_name=os.environ.get("DRIVER_B_NAME", "Driver B"),
        device_id="SIM_B",
        individual_id=os.environ.get("DRIVER_B_INDIVIDUAL_ID")
    )
]

# Initialize components
gateway = TelemetryGateway(rigs, event_queue)
ws_publisher = WebSocketPublisher(socketio, event_queue)

# Add health endpoint
@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'gateway': gateway.get_status(),
        'queue_size': event_queue.qsize()
    })

if __name__ == '__main__':
    # Start components
    gateway.start()
    ws_publisher.start()

    # Start with SocketIO support
    logger.info(f"Starting dual-rig dashboard on {DEFAULT_SERVER_HOST}:{port}")
    socketio.run(
        app,
        host=DEFAULT_SERVER_HOST,
        port=port,
        debug=False,
        use_reloader=False  # Important: prevents double-start
    )
```

### Phase 3: Data Cloud Integration (Week 3)

#### 3.1 Streaming Uploader with Batching

**New file:** `src/datacloud_uploader.py`

```python
"""
Data Cloud streaming uploader with batching and backoff
Respects 200KB limit and 250 RPS rate limits
"""

import logging
import time
import json
from queue import Queue, Empty
from typing import List, Dict
import threading
from collections import defaultdict

from datacloud_integration import DataCloudClient
from config import DATACLOUD_BATCH_SIZE, DATACLOUD_BATCH_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


class DataCloudUploader:
    """
    Batches and uploads telemetry events to Data Cloud
    Handles rate limiting, backoff, and retry logic
    """

    MAX_PAYLOAD_SIZE_BYTES = 200_000  # 200 KB limit
    UPLOAD_INTERVAL_MS = 350  # 350ms = ~3 uploads/sec per object
    MAX_RETRIES = 3

    def __init__(self, dc_client: DataCloudClient, event_queue: Queue):
        self.dc_client = dc_client
        self.event_queue = event_queue
        self.running = False

        # Separate batches per object type
        self.batches = {
            'telemetry': [],
            'laps': [],
            'sessions': [],
            'events': []
        }

        self.last_upload_time = defaultdict(float)
        self.retry_queue = Queue()
        self.stats = {
            'uploaded': 0,
            'failed': 0,
            'retried': 0,
            'rate_limited': 0
        }

    def start(self):
        """Start uploader thread"""
        self.running = True
        thread = threading.Thread(target=self._upload_loop, daemon=True)
        thread.start()
        logger.info("Data Cloud uploader started")

    def _upload_loop(self):
        """Main upload loop"""
        while self.running:
            try:
                # Process incoming events
                self._process_incoming_events()

                # Upload batches that are ready
                self._upload_ready_batches()

                # Process retry queue
                self._process_retries()

                time.sleep(0.01)  # 10ms tick

            except Exception as e:
                logger.error(f"Error in upload loop: {e}", exc_info=True)

    def _process_incoming_events(self):
        """Pull events from queue and add to batches"""
        events_processed = 0
        try:
            while events_processed < 50:  # Process up to 50 per cycle
                event = self.event_queue.get(timeout=0.001)
                self._route_to_batch(event)
                events_processed += 1
        except Empty:
            pass

    def _route_to_batch(self, event: dict):
        """Route event to appropriate batch based on type"""
        packet_id = event.get('packetId')

        # Route based on packet type
        if packet_id == 6:  # Car Telemetry
            batch_type = 'telemetry'
        elif packet_id == 2:  # Lap Data
            batch_type = 'laps'
        elif packet_id == 1:  # Session
            batch_type = 'sessions'
        elif packet_id == 3:  # Event
            batch_type = 'events'
        else:
            return  # Ignore other packet types

        # Transform to Data Cloud format
        dc_record = self._transform_to_dc_format(event, batch_type)
        if dc_record:
            self.batches[batch_type].append(dc_record)

    def _transform_to_dc_format(self, event: dict, batch_type: str) -> dict:
        """Transform event to Data Cloud record format"""
        rig_id = event.get('rig_id', 'UNKNOWN')
        session_uid = event.get('sessionUID', 0)
        overall_frame = event.get('overallFrameIdentifier', 0)
        packet_id = event.get('packetId', 0)
        car_index = event.get('playerCarIndex', 0)

        # Composite event ID
        event_id = f"{rig_id}:{session_uid}:{overall_frame}:{packet_id}:{car_index}"

        base_record = {
            'event_id': event_id,
            'device_fqid__c': rig_id,  # Foreign key to Device DMO
            'session_uid': str(session_uid),
            'overall_frame': overall_frame,
            'packet_id': packet_id,
            'car_index': car_index,
            'recordModified': event.get('timestamp_gateway_iso',
                                       time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime()))
        }

        if batch_type == 'telemetry':
            return {
                **base_record,
                'speed_kph': event.get('speed', 0),
                'throttle': event.get('throttle', 0),
                'brake': event.get('brake', 0),
                'gear': event.get('gear', 0),
                'engine_rpm': event.get('engineRPM', 0),
                'drs': event.get('drs', 0),
                'ers_store_energy': event.get('ersStoreEnergy', 0),
                # Tyre temps (FL, FR, RL, RR)
                'tyre_temp_fl': event.get('tyresSurfaceTemperature', [0]*4)[2],
                'tyre_temp_fr': event.get('tyresSurfaceTemperature', [0]*4)[3],
                'tyre_temp_rl': event.get('tyresSurfaceTemperature', [0]*4)[0],
                'tyre_temp_rr': event.get('tyresSurfaceTemperature', [0]*4)[1],
            }
        elif batch_type == 'laps':
            return {
                **base_record,
                'lap_number': event.get('currentLapNum', 0),
                'lap_time_ms': event.get('lastLapTimeInMS', 0),
                'car_position': event.get('carPosition', 0),
                'lap_invalid': event.get('currentLapInvalid', 0),
                'sector': event.get('sector', 0),
            }
        elif batch_type == 'sessions':
            return {
                **base_record,
                'track_id': event.get('trackId', -1),
                'session_type': event.get('sessionType', 0),
                'weather': event.get('weather', 0),
                'track_temperature': event.get('trackTemperature', 0),
                'air_temperature': event.get('airTemperature', 0),
            }

        return None

    def _upload_ready_batches(self):
        """Upload batches that meet size/time criteria"""
        current_time = time.time()

        for batch_type, records in self.batches.items():
            if not records:
                continue

            # Check if batch is ready (size or time)
            batch_size_bytes = len(json.dumps(records).encode('utf-8'))
            time_since_last_upload = (current_time - self.last_upload_time[batch_type]) * 1000

            should_upload = (
                batch_size_bytes >= self.MAX_PAYLOAD_SIZE_BYTES * 0.8 or  # 80% of limit
                time_since_last_upload >= self.UPLOAD_INTERVAL_MS or
                len(records) >= DATACLOUD_BATCH_SIZE
            )

            if should_upload:
                self._upload_batch(batch_type, records)
                self.batches[batch_type] = []  # Clear batch
                self.last_upload_time[batch_type] = current_time

    def _upload_batch(self, batch_type: str, records: List[dict]):
        """Upload a batch to Data Cloud"""
        try:
            logger.info(f"Uploading {len(records)} {batch_type} records to Data Cloud")

            # Use appropriate uploader method
            if batch_type == 'telemetry':
                self.dc_client._send_records('telemetry', records)
            elif batch_type == 'laps':
                self.dc_client._send_records('events', records)  # Use events endpoint
            elif batch_type == 'sessions':
                self.dc_client._send_records('sessions', records)
            elif batch_type == 'events':
                self.dc_client._send_records('events', records)

            self.stats['uploaded'] += len(records)

        except Exception as e:
            logger.error(f"Failed to upload {batch_type} batch: {e}")
            self.stats['failed'] += len(records)

            # Add to retry queue
            self.retry_queue.put({
                'batch_type': batch_type,
                'records': records,
                'attempts': 0,
                'next_retry': time.time() + 5  # Retry in 5 seconds
            })

    def _process_retries(self):
        """Process failed uploads in retry queue"""
        try:
            while not self.retry_queue.empty():
                retry_item = self.retry_queue.get(timeout=0.001)

                # Check if it's time to retry
                if time.time() < retry_item['next_retry']:
                    self.retry_queue.put(retry_item)  # Put back
                    break

                # Attempt retry
                retry_item['attempts'] += 1
                if retry_item['attempts'] > self.MAX_RETRIES:
                    logger.error(f"Max retries exceeded for {retry_item['batch_type']}, dropping batch")
                    continue

                try:
                    self._upload_batch(retry_item['batch_type'], retry_item['records'])
                    self.stats['retried'] += len(retry_item['records'])
                except Exception as e:
                    # Exponential backoff
                    backoff = min(60, 5 * (2 ** retry_item['attempts']))
                    retry_item['next_retry'] = time.time() + backoff
                    self.retry_queue.put(retry_item)
                    logger.warning(f"Retry failed, backing off for {backoff}s")
        except Empty:
            pass
```

### Phase 4: Dashboard UI (Week 4)

#### 4.1 Dual-Rig Dashboard Template

**New file:** `templates/dual_rig_dashboard.html`

```html
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dual-Rig F1 Telemetry Dashboard</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/dual-rig-style.css') }}">
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>
<body>
    <div class="dashboard-container">
        <!-- Header -->
        <header class="dashboard-header">
            <div class="connection-status">
                <span class="status-indicator" id="connectionStatus"></span>
                <span id="connectionText">Connecting...</span>
            </div>
        </header>

        <!-- Main Content: Split View -->
        <div class="split-view">
            <!-- Rig A Panel -->
            <div class="rig-panel" id="rigAPanel">
                <div class="rig-header">
                    <h2>🔴 RIG A</h2>
                    <div class="rig-status" id="rigAStatus">Waiting for data...</div>
                </div>

                <div class="telemetry-grid">
                    <!-- Speed & RPM -->
                    <div class="metric-card">
                        <h3>Speed</h3>
                        <div class="metric-value large" id="rigA-speed">0</div>
                        <div class="metric-unit">km/h</div>
                    </div>

                    <div class="metric-card">
                        <h3>RPM</h3>
                        <div class="metric-value large" id="rigA-rpm">0</div>
                        <canvas id="rigA-rpmGauge"></canvas>
                    </div>

                    <!-- Gear & Throttle/Brake -->
                    <div class="metric-card">
                        <h3>Gear</h3>
                        <div class="metric-value gear" id="rigA-gear">N</div>
                    </div>

                    <div class="metric-card">
                        <h3>Inputs</h3>
                        <div class="input-bars">
                            <div class="input-bar">
                                <label>Throttle</label>
                                <div class="bar-container">
                                    <div class="bar throttle" id="rigA-throttleBar"></div>
                                </div>
                                <span id="rigA-throttle">0%</span>
                            </div>
                            <div class="input-bar">
                                <label>Brake</label>
                                <div class="bar-container">
                                    <div class="bar brake" id="rigA-brakeBar"></div>
                                </div>
                                <span id="rigA-brake">0%</span>
                            </div>
                        </div>
                    </div>

                    <!-- Tyre Temps -->
                    <div class="metric-card tyre-grid">
                        <h3>Tyre Temps (°C)</h3>
                        <div class="tyres">
                            <div class="tyre-row">
                                <div class="tyre" id="rigA-tyreFL">
                                    <span class="tyre-label">FL</span>
                                    <span class="tyre-temp">--</span>
                                </div>
                                <div class="tyre" id="rigA-tyreFR">
                                    <span class="tyre-label">FR</span>
                                    <span class="tyre-temp">--</span>
                                </div>
                            </div>
                            <div class="tyre-row">
                                <div class="tyre" id="rigA-tyreRL">
                                    <span class="tyre-label">RL</span>
                                    <span class="tyre-temp">--</span>
                                </div>
                                <div class="tyre" id="rigA-tyreRR">
                                    <span class="tyre-label">RR</span>
                                    <span class="tyre-temp">--</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Position & Lap -->
                    <div class="metric-card">
                        <h3>Position</h3>
                        <div class="metric-value position" id="rigA-position">--</div>
                    </div>

                    <div class="metric-card">
                        <h3>Last Lap</h3>
                        <div class="metric-value lap-time" id="rigA-lapTime">--:--.---</div>
                    </div>
                </div>
            </div>

            <!-- Rig B Panel (mirror of Rig A) -->
            <div class="rig-panel" id="rigBPanel">
                <!-- Same structure as Rig A with rigB- IDs -->
                <!-- ... -->
            </div>
        </div>

        <!-- Event Timeline (shared) -->
        <div class="event-timeline">
            <h3>📋 Event Timeline</h3>
            <div class="events" id="eventTimeline"></div>
        </div>
    </div>

    <script src="{{ url_for('static', filename='js/dual-rig-dashboard.js') }}"></script>
</body>
</html>
```

#### 4.2 WebSocket Client JavaScript

**New file:** `static/js/dual-rig-dashboard.js`

```javascript
// WebSocket connection
const socket = io();

// Rig state
const rigState = {
    RIG_A: {},
    RIG_B: {}
};

// Connect handler
socket.on('connect', () => {
    console.log('Connected to telemetry gateway');
    updateConnectionStatus('connected');

    // Subscribe to both rigs
    socket.emit('subscribe_rig', { rig_id: 'RIG_A' });
    socket.emit('subscribe_rig', { rig_id: 'RIG_B' });
});

// Disconnect handler
socket.on('disconnect', () => {
    console.log('Disconnected from gateway');
    updateConnectionStatus('disconnected');
});

// Telemetry update handler
socket.on('telemetry_update', (data) => {
    const rigId = data.rig_id;
    if (!rigId) return;

    rigState[rigId] = data;
    updateRigDisplay(rigId, data);
});

function updateRigDisplay(rigId, data) {
    const prefix = rigId === 'RIG_A' ? 'rigA' : 'rigB';

    // Update speed
    updateElement(`${prefix}-speed`, Math.round(data.speed || 0));

    // Update RPM
    updateElement(`${prefix}-rpm`, Math.round(data.engineRPM || 0));

    // Update gear
    const gear = data.gear === 0 ? 'N' : data.gear === -1 ? 'R' : data.gear || 'N';
    updateElement(`${prefix}-gear`, gear);

    // Update throttle/brake bars
    const throttle = (data.throttle || 0) * 100;
    const brake = (data.brake || 0) * 100;
    updateProgressBar(`${prefix}-throttleBar`, throttle);
    updateProgressBar(`${prefix}-brakeBar`, brake);
    updateElement(`${prefix}-throttle`, `${Math.round(throttle)}%`);
    updateElement(`${prefix}-brake`, `${Math.round(brake)}%`);

    // Update tyre temps (FL, FR, RL, RR = indices 2, 3, 0, 1)
    if (data.tyresSurfaceTemperature) {
        const temps = data.tyresSurfaceTemperature;
        updateTyre(`${prefix}-tyreFL`, temps[2]);
        updateTyre(`${prefix}-tyreFR`, temps[3]);
        updateTyre(`${prefix}-tyreRL`, temps[0]);
        updateTyre(`${prefix}-tyreRR`, temps[1]);
    }

    // Update position
    updateElement(`${prefix}-position`, data.carPosition || '--');

    // Update lap time
    const lapTime = formatLapTime(data.lastLapTimeInMS);
    updateElement(`${prefix}-lapTime`, lapTime);
}

function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

function updateProgressBar(id, percentage) {
    const bar = document.getElementById(id);
    if (bar) {
        bar.style.width = `${percentage}%`;
    }
}

function updateTyre(id, temp) {
    const tyre = document.getElementById(id);
    if (!tyre) return;

    const tempSpan = tyre.querySelector('.tyre-temp');
    if (tempSpan) {
        tempSpan.textContent = Math.round(temp || 0);
    }

    // Color coding
    tyre.classList.remove('cold', 'optimal', 'hot');
    if (temp < 80) tyre.classList.add('cold');
    else if (temp > 105) tyre.classList.add('hot');
    else tyre.classList.add('optimal');
}

function formatLapTime(ms) {
    if (!ms || ms <= 0) return '--:--.---';
    const totalSeconds = ms / 1000;
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = (totalSeconds % 60).toFixed(3);
    return `${minutes}:${seconds.padStart(6, '0')}`;
}

function updateConnectionStatus(status) {
    const indicator = document.getElementById('connectionStatus');
    const text = document.getElementById('connectionText');

    indicator.className = `status-indicator ${status}`;
    text.textContent = status.charAt(0).toUpperCase() + status.slice(1);
}
```

---

## Network Configuration

### Sim PC Setup (Both Rigs)

**F1 25 Game Settings:**
```
Settings → Telemetry Settings
├─ UDP Telemetry: ON
├─ UDP Format: 2025
├─ UDP Send Rate: 60 Hz
├─ Broadcast Mode: OFF (use specific IP)
├─ IP Address: 192.168.1.100 (Host PC IP)
└─ UDP Port:
   ├─ Rig A: 20777
   └─ Rig B: 20778
```

**Alternative: Broadcast Mode**
```
└─ Broadcast Mode: ON
   └─ Subnet: 192.168.1.255
```
(Host listens on both ports; auto-detects source by IP)

### Host PC Environment Variables

**`.env` configuration:**
```bash
# Rig A Configuration
DRIVER_A_NAME="Lewis Hamilton"
DRIVER_A_INDIVIDUAL_ID="unified_individual_001"

# Rig B Configuration
DRIVER_B_NAME="Max Verstappen"
DRIVER_B_INDIVIDUAL_ID="unified_individual_002"

# Data Cloud Configuration
DATACLOUD_ENABLED=true
SALESFORCE_DOMAIN=your-org.my.salesforce.com
SF_CLIENT_ID=your_connected_app_client_id
SF_PRIVATE_KEY_PATH=./private.key
SF_USERNAME=your-salesforce-username@domain.com

# Data Cloud Streaming Endpoints
DC_TELEMETRY_ENDPOINT=https://subdomain.c360a.salesforce.com/api/v1/ingest/sources/F1Telemetry/TelemetryEvent
DC_EVENTS_ENDPOINT=https://subdomain.c360a.salesforce.com/api/v1/ingest/sources/F1Telemetry/LapEvent
DC_SESSIONS_ENDPOINT=https://subdomain.c360a.salesforce.com/api/v1/ingest/sources/F1Telemetry/SessionEvent
```

---

## Data Cloud Schema

### Data Streams Configuration

**TelemetryEvent__dlm** (high frequency, partial upsert enabled)
```yaml
apiName: TelemetryEvent__dlm
connector: F1Telemetry_Connector
refreshMode: Streaming
refreshType: Partial
primaryKey: event_id
schema:
  - event_id (Text, Required)
  - device_fqid__c (Text, Required, FK to Device DMO)
  - session_uid (Text)
  - overall_frame (Number)
  - speed_kph (Number)
  - throttle (Number, 0-1)
  - brake (Number, 0-1)
  - gear (Number)
  - engine_rpm (Number)
  - tyre_temp_fl (Number)
  - tyre_temp_fr (Number)
  - tyre_temp_rl (Number)
  - tyre_temp_rr (Number)
  - drs (Number, 0-1)
  - recordModified (DateTime, Required)
```

**LapEvent__dlm** (lap completions)
```yaml
apiName: LapEvent__dlm
connector: F1Telemetry_Connector
refreshMode: Streaming
refreshType: Partial
primaryKey: event_id
schema:
  - event_id (Text, Required)
  - device_fqid__c (Text, Required)
  - session_uid (Text)
  - lap_number (Number)
  - lap_time_ms (Number)
  - car_position (Number)
  - lap_invalid (Boolean)
  - recordModified (DateTime, Required)
```

---

## Deployment

### Running the System

```bash
# Install dependencies
pip install -r config/requirements.txt

# Install WebSocket support
pip install flask-socketio python-socketio

# Set environment variables
cp config/.env.example .env
# Edit .env with your configuration

# Run the gateway
python3 scripts/run_dual_rig_dashboard.py
```

**New launcher:** `scripts/run_dual_rig_dashboard.py`

```python
#!/usr/bin/env python3
"""
Dual-rig telemetry dashboard launcher
Starts all components in correct order
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from app import app, socketio, gateway, ws_publisher, event_queue
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    try:
        # Start components
        logger.info("Starting dual-rig telemetry gateway...")
        gateway.start()
        ws_publisher.start()

        # Start Flask with SocketIO
        port = int(os.environ.get("PORT", 8080))
        logger.info(f"Dashboard available at http://localhost:{port}")

        socketio.run(
            app,
            host='0.0.0.0',
            port=port,
            debug=False,
            use_reloader=False
        )
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
```

---

## Monitoring & Observability

### Metrics Endpoint

Add to `app.py`:

```python
@app.route('/metrics')
def metrics():
    """Prometheus-style metrics endpoint"""
    return Response(
        f"""# HELP f1_packets_received Total packets received per rig
# TYPE f1_packets_received counter
f1_packets_received{{rig="RIG_A"}} {gateway.receivers['RIG_A']['receiver'].packet_count}
f1_packets_received{{rig="RIG_B"}} {gateway.receivers['RIG_B']['receiver'].packet_count}

# HELP f1_event_queue_size Current event queue size
# TYPE f1_event_queue_size gauge
f1_event_queue_size {event_queue.qsize()}

# HELP f1_datacloud_uploaded Total records uploaded to Data Cloud
# TYPE f1_datacloud_uploaded counter
f1_datacloud_uploaded {dc_uploader.stats['uploaded']}

# HELP f1_datacloud_failed Total failed uploads
# TYPE f1_datacloud_failed counter
f1_datacloud_failed {dc_uploader.stats['failed']}
""",
        mimetype='text/plain'
    )
```

---

## Key Improvements Over Single-Rig Architecture

1. **Scalability**: Easily add more rigs by adding RigConfig entries
2. **Isolation**: Each rig has independent receiver thread and packet processing
3. **Real-time Distribution**: WebSocket pub/sub allows efficient multi-client updates
4. **Proper Batching**: Data Cloud uploader respects size/rate limits with backoff
5. **Event Correlation**: Session registry tracks which rig owns each sessionUID
6. **Observability**: Metrics endpoint for monitoring system health
7. **Resilience**: Retry queue with exponential backoff for failed uploads
8. **Clean Separation**: Gateway → Publisher → Dashboard → Data Cloud are decoupled

---

## Next Steps

1. **Week 1**: Implement TelemetryGateway and multi-receiver support
2. **Week 2**: Add WebSocket publisher and update dashboard
3. **Week 3**: Implement Data Cloud uploader with proper batching
4. **Week 4**: Build dual-rig UI and test end-to-end

Want me to start implementing any of these components?
