"""
Multi-rig telemetry gateway
Manages multiple UDP receivers and routes packets to processors
"""

import logging
import time
from typing import Dict, Optional, Callable, List
from dataclasses import dataclass
from queue import Queue
import threading

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
    Each rig gets its own UDP listener on a separate port
    """

    def __init__(self, rigs: List[RigConfig], event_callback: Optional[Callable] = None):
        """
        Initialize gateway with rig configurations

        Args:
            rigs: List of RigConfig objects
            event_callback: Optional callback function(rig_id, packet_data)
        """
        self.rigs = rigs
        self.event_callback = event_callback
        self.receivers = {}
        self.receiver_threads = {}
        self.active_sessions = {}  # sessionUID -> rig_id mapping
        self.running = False
        self.stats = {
            rig.rig_id: {
                'packets_received': 0,
                'last_packet_time': None,
                'active': False,
                'current_session': None
            } for rig in rigs
        }

    def start(self):
        """Start all receivers in separate threads"""
        logger.info(f"Starting telemetry gateway with {len(self.rigs)} rigs")
        self.running = True

        # Import here to avoid circular dependency
        from receiver_multi import F1TelemetryReceiverMulti

        for rig in self.rigs:
            logger.info(f"Starting receiver for {rig.rig_id} on port {rig.udp_port}")

            # Create receiver with callback
            receiver = F1TelemetryReceiverMulti(
                rig_id=rig.rig_id,
                port=rig.udp_port,
                driver_name=rig.driver_name,
                packet_callback=lambda rig_id, data: self._on_packet_received(rig_id, data, rig)
            )

            # Start receiver in its own thread
            thread = threading.Thread(
                target=receiver.run,
                name=f"Receiver-{rig.rig_id}",
                daemon=True
            )
            thread.start()

            self.receivers[rig.rig_id] = receiver
            self.receiver_threads[rig.rig_id] = thread
            self.stats[rig.rig_id]['active'] = True

            logger.info(f"✓ {rig.rig_id} receiver started on port {rig.udp_port}")

        logger.info("All receivers started successfully")

    def _on_packet_received(self, rig_id: str, packet_data: dict, rig_config: RigConfig):
        """
        Callback when a receiver processes a packet
        Enriches with rig metadata and forwards to application
        """
        # Update stats
        self.stats[rig_id]['packets_received'] += 1
        self.stats[rig_id]['last_packet_time'] = time.time()

        # Enrich packet with rig identification
        enriched_packet = {
            **packet_data,
            'rig_id': rig_id,
            'device_id': rig_config.device_id,
            'driver_name': rig_config.driver_name,
            'individual_id': rig_config.individual_id,
            'source_type': 'f1_25',
            'timestamp_gateway': time.time(),
            'timestamp_gateway_iso': time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
        }

        # Track active sessions
        session_uid = packet_data.get('sessionUID')
        if session_uid:
            if session_uid not in self.active_sessions:
                self.active_sessions[session_uid] = rig_id
                logger.info(f"🏁 New session {session_uid} started on {rig_id}")

            self.stats[rig_id]['current_session'] = session_uid

        # Forward to application callback
        if self.event_callback:
            try:
                self.event_callback(rig_id, enriched_packet)
            except Exception as e:
                logger.error(f"Error in event callback for {rig_id}: {e}")

    def get_status(self) -> dict:
        """Get status of all receivers"""
        status = {
            'running': self.running,
            'active_sessions': len(self.active_sessions),
            'total_rigs': len(self.rigs),
            'rigs': {}
        }

        for rig_id, stats in self.stats.items():
            receiver = self.receivers.get(rig_id)
            status['rigs'][rig_id] = {
                'packets_received': stats['packets_received'],
                'last_packet_time': stats['last_packet_time'],
                'last_packet_age_seconds': (
                    time.time() - stats['last_packet_time']
                    if stats['last_packet_time'] else None
                ),
                'active': stats['active'] and receiver is not None,
                'current_session': stats['current_session'],
                'thread_alive': (
                    self.receiver_threads.get(rig_id).is_alive()
                    if rig_id in self.receiver_threads else False
                )
            }

        return status

    def stop(self):
        """Stop all receivers"""
        logger.info("Stopping telemetry gateway")
        self.running = False

        for rig_id, receiver in self.receivers.items():
            try:
                receiver.stop()
                logger.info(f"Stopped receiver for {rig_id}")
            except Exception as e:
                logger.error(f"Error stopping receiver {rig_id}: {e}")

        self.receivers.clear()
        self.receiver_threads.clear()

    def get_rig_stats(self, rig_id: str) -> Optional[dict]:
        """Get statistics for a specific rig"""
        return self.stats.get(rig_id)

    def is_rig_active(self, rig_id: str) -> bool:
        """Check if a rig is actively sending data"""
        stats = self.stats.get(rig_id)
        if not stats or not stats['last_packet_time']:
            return False

        # Consider active if received packet in last 5 seconds
        age = time.time() - stats['last_packet_time']
        return age < 5.0
