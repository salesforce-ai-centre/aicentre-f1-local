"""
WebSocket publisher for real-time dual-rig dashboard updates
"""

from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
import logging
import time
from collections import defaultdict

logger = logging.getLogger(__name__)


class WebSocketPublisher:
    """
    Publishes telemetry events via WebSocket
    Supports per-rig subscriptions and aggregated views
    """

    def __init__(self, socketio: SocketIO):
        """
        Initialize WebSocket publisher

        Args:
            socketio: Flask-SocketIO instance
        """
        self.socketio = socketio
        self.last_state = {}  # rig_id -> last published state
        self.client_count = 0

        # Aggregated state by packet type per rig
        self.aggregated_state = defaultdict(dict)

        # Register SocketIO event handlers
        self._register_handlers()

        logger.info("WebSocket publisher initialized")

    def _register_handlers(self):
        """Register WebSocket event handlers"""

        @self.socketio.on('connect')
        def handle_connect():
            self.client_count += 1
            logger.info(f"Client connected: {request.sid} (total: {self.client_count})")
            emit('connection_status', {'status': 'connected'})

            # Send current state immediately for all rigs
            for rig_id, state in self.aggregated_state.items():
                emit('telemetry_update', {
                    'rig_id': rig_id,
                    **state
                })

        @self.socketio.on('disconnect')
        def handle_disconnect():
            self.client_count -= 1
            logger.info(f"Client disconnected: {request.sid} (total: {self.client_count})")

        @self.socketio.on('subscribe_rig')
        def handle_subscribe_rig(data):
            """Subscribe to specific rig updates"""
            rig_id = data.get('rig_id')
            if rig_id:
                join_room(rig_id)
                logger.info(f"Client {request.sid} subscribed to {rig_id}")

                # Send current state immediately
                if rig_id in self.aggregated_state:
                    emit('telemetry_update', {
                        'rig_id': rig_id,
                        **self.aggregated_state[rig_id]
                    })

        @self.socketio.on('subscribe_all')
        def handle_subscribe_all():
            """Subscribe to all rigs"""
            join_room('all')
            logger.info(f"Client {request.sid} subscribed to all rigs")

            # Send current state for all rigs
            for rig_id, state in self.aggregated_state.items():
                emit('telemetry_update', {
                    'rig_id': rig_id,
                    **state
                })

        @self.socketio.on('unsubscribe_rig')
        def handle_unsubscribe_rig(data):
            """Unsubscribe from rig updates"""
            rig_id = data.get('rig_id')
            if rig_id:
                leave_room(rig_id)
                logger.info(f"Client {request.sid} unsubscribed from {rig_id}")

    def on_telemetry_packet(self, rig_id: str, packet_data: dict):
        """
        Process incoming telemetry packet and broadcast to subscribers

        Args:
            rig_id: Rig identifier
            packet_data: Telemetry packet data
        """
        # Update aggregated state (merge packet data by type)
        current_state = self.aggregated_state[rig_id]

        # Merge new packet data into current state
        for key, value in packet_data.items():
            current_state[key] = value

        # Add rig_id to payload
        current_state['rig_id'] = rig_id
        current_state['last_update'] = time.time()

        # Debug: Log first few packets
        if not hasattr(self, '_debug_count'):
            self._debug_count = {}
        if rig_id not in self._debug_count:
            self._debug_count[rig_id] = 0

        self._debug_count[rig_id] += 1
        if self._debug_count[rig_id] <= 3:
            logger.info(f"📡 Broadcasting {rig_id} packet #{self._debug_count[rig_id]}: "
                       f"speed={current_state.get('speed')}, "
                       f"rpm={current_state.get('engineRPM')}, "
                       f"clients={self.client_count}")

        # Broadcast to specific rig subscribers
        self.socketio.emit(
            'telemetry_update',
            current_state,
            room=rig_id
        )

        # Also broadcast to 'all' room
        self.socketio.emit(
            'telemetry_update',
            current_state,
            room='all'
        )

    def get_stats(self) -> dict:
        """Get publisher statistics"""
        return {
            'connected_clients': self.client_count,
            'active_rigs': len(self.aggregated_state),
            'rigs': list(self.aggregated_state.keys())
        }
