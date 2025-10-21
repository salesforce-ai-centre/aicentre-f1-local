"""
Multi-instance F1 telemetry receiver with callback support
Based on receiver.py but designed for parallel operation
"""

import socket
import struct
import time
import logging
from typing import Optional, Callable, Dict, Any

from receiver import (
    PacketHeader, PacketLapData, PacketCarTelemetry,
    PacketCarStatus, PacketCarDamage, PacketSessionData,
    PACKET_ID_MOTION, PACKET_ID_SESSION, PACKET_ID_LAP_DATA,
    PACKET_ID_CAR_TELEMETRY, PACKET_ID_CAR_STATUS, PACKET_ID_CAR_DAMAGE
)

logger = logging.getLogger(__name__)

# F1 Track ID to Name mapping
TRACK_NAMES = {
    0: "Melbourne", 1: "Paul Ricard", 2: "Shanghai", 3: "Sakhir (Bahrain)",
    4: "Catalunya", 5: "Monaco", 6: "Montreal", 7: "Silverstone",
    8: "Hockenheim", 9: "Hungaroring", 10: "Spa", 11: "Monza",
    12: "Singapore", 13: "Suzuka", 14: "Abu Dhabi", 15: "Texas",
    16: "Brazil", 17: "Austria", 18: "Sochi", 19: "Mexico",
    20: "Baku", 21: "Sakhir Short", 22: "Silverstone Short",
    23: "Texas Short", 24: "Suzuka Short", 25: "Hanoi",
    26: "Zandvoort", 27: "Imola", 28: "Portimão", 29: "Jeddah",
    30: "Miami", 31: "Las Vegas", 32: "Losail", -1: "Unknown"
}

SESSION_TYPES = {
    0: "Unknown", 1: "Practice 1", 2: "Practice 2", 3: "Practice 3",
    4: "Short Practice", 5: "Q1", 6: "Q2", 7: "Q3",
    8: "Short Qualifying", 9: "One-Shot Q", 10: "Sprint Shootout 1",
    11: "Sprint Shootout 2", 12: "Sprint Shootout 3", 15: "Sprint",
    16: "Sprint 2", 17: "Race", 18: "Race 2", 19: "Race 3", 20: "Time Trial"
}


class F1TelemetryReceiverMulti:
    """
    F1 Telemetry receiver designed for multi-instance operation
    Each instance listens on its own UDP port and calls back with processed data
    """

    def __init__(self, rig_id: str, port: int, driver_name: str,
                 packet_callback: Callable[[str, dict], None]):
        """
        Initialize receiver

        Args:
            rig_id: Unique identifier for this rig (e.g., "RIG_A")
            port: UDP port to listen on
            driver_name: Name of the driver
            packet_callback: Callback function(rig_id, packet_data)
        """
        self.rig_id = rig_id
        self.port = port
        self.driver_name = driver_name
        self.packet_callback = packet_callback

        self.socket = None
        self.running = False
        self.packet_count = 0
        self.last_packet_time = None

        # Packet state cache
        self.latest_lap_data = None
        self.latest_telemetry = None
        self.latest_status = None
        self.latest_damage = None
        self.latest_session = None
        self.latest_header = None

        logger.info(f"Initialized receiver for {rig_id} (driver: {driver_name}, port: {port})")

    def run(self):
        """Main receiver loop"""
        logger.info(f"[{self.rig_id}] Starting UDP receiver on port {self.port}")

        try:
            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('0.0.0.0', self.port))
            self.socket.settimeout(1.0)  # 1 second timeout for clean shutdown

            self.running = True
            logger.info(f"[{self.rig_id}] ✓ Listening on 0.0.0.0:{self.port}")

            while self.running:
                try:
                    data, addr = self.socket.recvfrom(2048)
                    self._process_packet(data)
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:  # Only log if not shutting down
                        logger.error(f"[{self.rig_id}] Error receiving packet: {e}")

        except Exception as e:
            logger.error(f"[{self.rig_id}] Fatal error in receiver: {e}", exc_info=True)
        finally:
            self._cleanup()

    def _process_packet(self, data: bytes):
        """Process a received UDP packet"""
        if len(data) < PacketHeader.SIZE:
            return

        # Parse packet header
        header = PacketHeader.from_bytes(data)
        if not header:
            return

        self.packet_count += 1
        self.last_packet_time = time.time()
        self.latest_header = header

        # Route to appropriate handler
        packet_id = header.m_packetId
        payload = data[PacketHeader.SIZE:]

        try:
            if packet_id == PACKET_ID_LAP_DATA:
                self._handle_lap_data(header, payload)
            elif packet_id == PACKET_ID_CAR_TELEMETRY:
                self._handle_car_telemetry(header, payload)
            elif packet_id == PACKET_ID_CAR_STATUS:
                self._handle_car_status(header, payload)
            elif packet_id == PACKET_ID_CAR_DAMAGE:
                self._handle_car_damage(header, payload)
            elif packet_id == PACKET_ID_SESSION:
                self._handle_session(header, payload)
        except Exception as e:
            logger.debug(f"[{self.rig_id}] Error processing packet {packet_id}: {e}")

    def _handle_lap_data(self, header: PacketHeader, payload: bytes):
        """Process lap data packet"""
        packet = PacketLapData.from_bytes(header, payload)
        if not packet or not packet.m_lapData:
            return

        self.latest_lap_data = packet
        player_index = header.m_playerCarIndex

        if player_index < len(packet.m_lapData):
            player_lap = packet.m_lapData[player_index]
            self._send_callback({
                'packetId': PACKET_ID_LAP_DATA,
                'sessionUID': header.m_sessionUID,
                'sessionTime': header.m_sessionTime,
                'frameIdentifier': header.m_frameIdentifier,
                'overallFrameIdentifier': header.m_overallFrameIdentifier,
                'playerCarIndex': player_index,
                'lastLapTimeInMS': player_lap.m_lastLapTimeInMS,
                'currentLapTimeInMS': player_lap.m_currentLapTimeInMS,
                'currentLapNum': player_lap.m_currentLapNum,
                'carPosition': player_lap.m_carPosition + 1,  # Convert to 1-indexed
                'sector': player_lap.m_sector,
                'currentLapInvalid': player_lap.m_currentLapInvalid,
                'pitStatus': player_lap.m_pitStatus,
                'lapDistance': player_lap.m_lapDistance,
            })

    def _handle_car_telemetry(self, header: PacketHeader, payload: bytes):
        """Process car telemetry packet"""
        packet = PacketCarTelemetry.from_bytes(header, payload)
        if not packet or not packet.m_carTelemetryData:
            return

        self.latest_telemetry = packet
        player_index = header.m_playerCarIndex

        if player_index < len(packet.m_carTelemetryData):
            player_telem = packet.m_carTelemetryData[player_index]
            self._send_callback({
                'packetId': PACKET_ID_CAR_TELEMETRY,
                'sessionUID': header.m_sessionUID,
                'sessionTime': header.m_sessionTime,
                'frameIdentifier': header.m_frameIdentifier,
                'overallFrameIdentifier': header.m_overallFrameIdentifier,
                'playerCarIndex': player_index,
                'speed': player_telem.m_speed,
                'throttle': player_telem.m_throttle,
                'brake': player_telem.m_brake,
                'steer': player_telem.m_steer,
                'gear': player_telem.m_gear,
                'engineRPM': player_telem.m_engineRPM,
                'drs': player_telem.m_drs,
                'revLightsPercent': player_telem.m_revLightsPercent,
                'brakesTemperature': player_telem.m_brakesTemperature,
                'tyresSurfaceTemperature': player_telem.m_tyresSurfaceTemperature,
                'tyresInnerTemperature': player_telem.m_tyresInnerTemperature,
                'engineTemperature': player_telem.m_engineTemperature,
                'tyresPressure': player_telem.m_tyresPressure,
            })

    def _handle_car_status(self, header: PacketHeader, payload: bytes):
        """Process car status packet"""
        packet = PacketCarStatus.from_bytes(header, payload)
        if not packet or not packet.m_carStatusData:
            return

        self.latest_status = packet
        player_index = header.m_playerCarIndex

        if player_index < len(packet.m_carStatusData):
            player_status = packet.m_carStatusData[player_index]
            self._send_callback({
                'packetId': PACKET_ID_CAR_STATUS,
                'sessionUID': header.m_sessionUID,
                'sessionTime': header.m_sessionTime,
                'frameIdentifier': header.m_frameIdentifier,
                'overallFrameIdentifier': header.m_overallFrameIdentifier,
                'playerCarIndex': player_index,
                'fuelInTank': player_status.m_fuelInTank,
                'fuelCapacity': player_status.m_fuelCapacity,
                'fuelRemainingLaps': player_status.m_fuelRemainingLaps,
                'drsAllowed': player_status.m_drsAllowed,
                'ersStoreEnergy': player_status.m_ersStoreEnergy,
                'ersDeployMode': player_status.m_ersDeployMode,
                'actualTyreCompound': player_status.m_actualTyreCompound,
                'tyresAgeLaps': player_status.m_tyresAgeLaps,
            })

    def _handle_car_damage(self, header: PacketHeader, payload: bytes):
        """Process car damage packet"""
        packet = PacketCarDamage.from_bytes(header, payload)
        if not packet or not packet.m_carDamageData:
            return

        self.latest_damage = packet
        player_index = header.m_playerCarIndex

        if player_index < len(packet.m_carDamageData):
            player_damage = packet.m_carDamageData[player_index]
            self._send_callback({
                'packetId': PACKET_ID_CAR_DAMAGE,
                'sessionUID': header.m_sessionUID,
                'sessionTime': header.m_sessionTime,
                'frameIdentifier': header.m_frameIdentifier,
                'overallFrameIdentifier': header.m_overallFrameIdentifier,
                'playerCarIndex': player_index,
                'tyresWear': player_damage.m_tyresWear,
                'frontLeftWingDamage': player_damage.m_frontLeftWingDamage,
                'frontRightWingDamage': player_damage.m_frontRightWingDamage,
                'rearWingDamage': player_damage.m_rearWingDamage,
                'floorDamage': player_damage.m_floorDamage,
                'diffuserDamage': player_damage.m_diffuserDamage,
                'sidepodDamage': player_damage.m_sidepodDamage,
                'gearBoxDamage': player_damage.m_gearBoxDamage,
                'engineDamage': player_damage.m_engineDamage,
                'drsFault': player_damage.m_drsFault,
                'ersFault': player_damage.m_ersFault,
            })

    def _handle_session(self, header: PacketHeader, payload: bytes):
        """Process session packet"""
        packet = PacketSessionData.from_bytes(header, payload)
        if not packet:
            return

        self.latest_session = packet
        self._send_callback({
            'packetId': PACKET_ID_SESSION,
            'sessionUID': header.m_sessionUID,
            'sessionTime': header.m_sessionTime,
            'frameIdentifier': header.m_frameIdentifier,
            'overallFrameIdentifier': header.m_overallFrameIdentifier,
            'weather': packet.m_weather,
            'trackTemperature': packet.m_trackTemperature,
            'airTemperature': packet.m_airTemperature,
            'totalLaps': packet.m_totalLaps,
            'trackLength': packet.m_trackLength,
            'sessionType': packet.m_sessionType,
            'trackId': packet.m_trackId,
            'trackName': TRACK_NAMES.get(packet.m_trackId, "Unknown"),
            'sessionTypeName': SESSION_TYPES.get(packet.m_sessionType, "Unknown"),
        })

    def _send_callback(self, packet_data: dict):
        """Send processed packet data to callback"""
        if self.packet_callback:
            try:
                self.packet_callback(self.rig_id, packet_data)
            except Exception as e:
                logger.error(f"[{self.rig_id}] Error in packet callback: {e}")

    def stop(self):
        """Stop the receiver"""
        logger.info(f"[{self.rig_id}] Stopping receiver")
        self.running = False

    def _cleanup(self):
        """Clean up socket resources"""
        if self.socket:
            try:
                self.socket.close()
                logger.info(f"[{self.rig_id}] Socket closed")
            except Exception as e:
                logger.error(f"[{self.rig_id}] Error closing socket: {e}")

    def get_packet_count(self) -> int:
        """Get total packets received"""
        return self.packet_count

    def get_last_packet_time(self) -> Optional[float]:
        """Get timestamp of last received packet"""
        return self.last_packet_time

    def is_active(self) -> bool:
        """Check if receiver is actively receiving packets"""
        if not self.last_packet_time:
            return False
        age = time.time() - self.last_packet_time
        return age < 5.0  # Active if received packet in last 5 seconds
