#python receiver.py --url https://f1-dashboard-f1208f7ee582.herokuapp.com/data --driver “Jacob” --track “Bahrain”

import socket
import struct
import datetime
import requests
import uuid
import time
import json
import concurrent.futures
import sys
import argparse
import logging
import os
import psutil
import threading
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from dotenv import load_dotenv
from datacloud_integration import create_datacloud_client

# --- Constants ---
APP_NAME = "F1 24 Telemetry Bridge"
DEFAULT_UDP_IP = "0.0.0.0"
DEFAULT_UDP_PORT = 20777
DEFAULT_DRIVER_NAME = "Salesforce Guest"
DEFAULT_TRACK_NAME = "Bahrain"
DEFAULT_SEND_INTERVAL_S = 0.01  # Ultra-fast 10ms updates for local-only operation
MAX_SEND_INTERVAL_S = 5.0
MAX_SEND_RETRIES = 3
RETRY_BACKOFF_FACTOR = 1.5
BACKOFF_RESET_THRESHOLD = MAX_SEND_RETRIES + 3 # Retries after which backoff interval resets
SOCKET_TIMEOUT_S = 1.0
STATUS_UPDATE_INTERVAL_S = 60.0
PACKET_BUFFER_SIZE = 2048

# Performance optimization constants
LOG_THROTTLE_INTERVAL = 10.0  # Only log debug messages every 10 seconds
STATUS_LOG_INTERVAL = 30.0    # Status updates every 30 seconds instead of 60
PERFORMANCE_MODE = False      # Disable performance optimizations temporarily

# Packet IDs (From F1 24 Spec Page 2/3)
PACKET_ID_MOTION = 0
PACKET_ID_SESSION = 1
PACKET_ID_LAP_DATA = 2
PACKET_ID_EVENT = 3
PACKET_ID_PARTICIPANTS = 4
PACKET_ID_CAR_SETUPS = 5
PACKET_ID_CAR_TELEMETRY = 6
PACKET_ID_CAR_STATUS = 7
PACKET_ID_FINAL_CLASSIFICATION = 8
PACKET_ID_LOBBY_INFO = 9
PACKET_ID_CAR_DAMAGE = 10
PACKET_ID_SESSION_HISTORY = 11
PACKET_ID_TYRE_SETS = 12
PACKET_ID_MOTION_EX = 13
PACKET_ID_TIME_TRIAL = 14

# --- Data Structures (Dataclasses based on F1 24 Spec) ---

@dataclass
class PacketHeader:
    m_packetFormat: int
    m_gameYear: int
    m_gameMajorVersion: int
    m_gameMinorVersion: int
    m_packetVersion: int
    m_packetId: int
    m_sessionUID: int
    m_sessionTime: float
    m_frameIdentifier: int
    m_overallFrameIdentifier: int
    m_playerCarIndex: int
    m_secondaryPlayerCarIndex: int

    # Format verified against F1 24 Spec Page 2
    HEADER_FORMAT: str = "<HBBBBBQfIIBB"
    SIZE: int = struct.calcsize(HEADER_FORMAT)

    @classmethod
    def from_bytes(cls, data: bytes) -> Optional['PacketHeader']:
        if len(data) < cls.SIZE:
            return None
        try:
            unpacked = struct.unpack(cls.HEADER_FORMAT, data[:cls.SIZE])
            return cls(*unpacked)
        except struct.error as e:
            logging.error(f"Failed to unpack PacketHeader: {e}")
            return None

# --- LapData Structures (F1 24 Spec Pages 5-6) ---
@dataclass
class LapData:
    # Field names MUST match the exact structure from the F1 24 spec
    m_lastLapTimeInMS: int          # uint32
    m_currentLapTimeInMS: int       # uint32
    m_sector1TimeMSPart: int        # uint16
    m_sector1TimeMinutesPart: int   # uint8
    m_sector2TimeMSPart: int        # uint16
    m_sector2TimeMinutesPart: int   # uint8
    m_deltaToCarInFrontMSPart: int  # uint16
    m_deltaToCarInFrontMinutesPart: int # uint8
    m_deltaToRaceLeaderMSPart: int  # uint16
    m_deltaToRaceLeaderMinutesPart: int # uint8
    m_lapDistance: float            # float
    m_totalDistance: float          # float
    m_safetyCarDelta: float         # float
    m_carPosition: int              # uint8
    m_currentLapNum: int            # uint8
    m_pitStatus: int                # uint8
    m_numPitStops: int              # uint8
    m_sector: int                   # uint8
    m_currentLapInvalid: int        # uint8
    m_penalties: int                # uint8
    m_totalWarnings: int            # uint8
    m_cornerCuttingWarnings: int    # uint8
    m_numUnservedDriveThroughPens: int # uint8
    m_numUnservedStopGoPens: int    # uint8
    m_gridPosition: int             # uint8
    m_driverStatus: int             # uint8
    m_resultStatus: int             # uint8
    m_pitLaneTimerActive: int       # uint8
    m_pitLaneTimeInLaneInMS: int    # uint16
    m_pitStopTimerInMS: int         # uint16
    m_pitStopShouldServePen: int    # uint8
    m_speedTrapFastestSpeed: float  # float
    m_speedTrapFastestLap: int = 0  # uint8 (default to 0 if missing)

    # Format string exactly matching the F1 24 spec
    LAP_DATA_FORMAT: str = "<IIHBHBHBHBfffBBBBBBBBBBBBBBHHBfB"
    
    # Alternative format string for F1 24 if it's missing the last field
    LAP_DATA_FORMAT_NO_FASTEST_LAP: str = "<IIHBHBHBHBfffBBBBBBBBBBBBBBHHBf"
    
    # Use the format with all fields, adjust at runtime if needed
    SIZE: int = struct.calcsize(LAP_DATA_FORMAT_NO_FASTEST_LAP)

@dataclass
class PacketLapData:
    m_header: PacketHeader
    m_lapData: List[LapData] = field(default_factory=list)
    m_timeTrialPBCarIdx: Optional[int] = None # uint8 - Only relevant for TimeTrial Packet
    m_timeTrialRivalCarIdx: Optional[int] = None # uint8 - Only relevant for TimeTrial Packet

    PACKET_FORMAT: str = "" # Defined dynamically
    NUM_CARS = 22

    @classmethod
    def from_bytes(cls, header: PacketHeader, data: bytes) -> Optional['PacketLapData']:
        packet = cls(m_header=header)
        lap_data_bytes = data # For standard LapData packet

        required_lap_data_size = LapData.SIZE * cls.NUM_CARS

        # Check if the extra indices might be present (packet slightly longer)
        extra_indices_size = 2 # 2 * uint8
        if len(data) >= required_lap_data_size + extra_indices_size:
             try: # Add try-except for unpacking extra indices
                 indices = struct.unpack("<BB", data[required_lap_data_size : required_lap_data_size + extra_indices_size])
                 packet.m_timeTrialPBCarIdx = indices[0]
                 packet.m_timeTrialRivalCarIdx = indices[1]
                 logging.debug("Found and parsed extra TimeTrial indices.")
             except struct.error as e:
                 logging.warning(f"Could not unpack potential extra indices: {e}")
                 # Assume they aren't there or packet is malformed
             # Process only the lap data part for the main list
             lap_data_bytes = data[:required_lap_data_size]
             logging.debug(f"Adjusted lap_data_bytes length to {len(lap_data_bytes)} after finding potential extra indices.")
        elif len(data) < required_lap_data_size:
            logging.warning(f"LapData packet too short. Expected at least {required_lap_data_size}, got {len(data)}")
            return None

        # <<< DEBUGGING >>>
        logging.debug(f"Calculated LapData.SIZE: {LapData.SIZE}") # Check calculated size
        logging.debug(f"Expected LapData format string: {LapData.LAP_DATA_FORMAT}") # Verify format string
        # <<< END DEBUGGING >>>

        for i in range(cls.NUM_CARS):
            start = i * LapData.SIZE
            end = start + LapData.SIZE
            if end > len(lap_data_bytes):
                logging.warning(f"Insufficient data for lap data of car {i} (start={start}, end={end}, total_len={len(lap_data_bytes)})")
                break
            try:
                # <<< ENHANCED DEBUGGING >>>
                current_chunk = lap_data_bytes[start:end]
                expected_size = LapData.SIZE
                actual_size = len(current_chunk)
                # Use the format string without the last field
                format_str = LapData.LAP_DATA_FORMAT_NO_FASTEST_LAP
                # Count format codes, excluding endianness and padding codes
                num_format_codes = sum(c.isalpha() for c in format_str)

                logging.debug(f"--- Car {i} LapData Debug ---")
                logging.debug(f"Slicing: start={start}, end={end}")
                logging.debug(f"Expected Size: {expected_size}, Actual Slice Size: {actual_size}")
                logging.debug(f"Format String: '{format_str}' (Approx Codes: {num_format_codes})") # Updated count logic slightly
                if actual_size != expected_size:
                    logging.error(f"CRITICAL SIZE MISMATCH FOR CAR {i}! Skipping unpack.")
                    logging.debug(f"--> Hex Data (Size {actual_size}): {current_chunk.hex()}") # Show hex data if size mismatch
                    continue

                # Log the hex data *before* unpacking
                logging.debug(f"--> Hex Data to unpack (Size {actual_size}): {current_chunk.hex()}")

                lap_tuple = struct.unpack(format_str, current_chunk)
                actual_tuple_len = len(lap_tuple)
                logging.debug(f"Unpacked Tuple Length: {actual_tuple_len}")
                # <<< END ENHANCED DEBUGGING >>>

                # We need to adapt to whatever format F1 24 is sending
                try:
                    # The expected number of fields for F1 24 is 32 (all except m_speedTrapFastestLap)
                    expected_fields = 32
                    
                    if actual_tuple_len == expected_fields:
                        # If we get exactly the format we expect, use it directly
                        lap_entry = LapData(
                            *lap_tuple,
                            m_speedTrapFastestLap=0  # Default value for the last field
                        )
                        packet.m_lapData.append(lap_entry)
                        logging.debug(f"Car {i}: Successfully created LapData with {actual_tuple_len} fields + default")
                    
                    elif actual_tuple_len == expected_fields + 1:
                        # If we get a format with one more field than expected
                        lap_entry = LapData(*lap_tuple)
                        packet.m_lapData.append(lap_entry)
                        logging.debug(f"Car {i}: Successfully created LapData with full {actual_tuple_len} fields")
                    
                    elif actual_tuple_len == expected_fields - 1:
                        # If we get a format with one less field than expected
                        # Add both missing fields with defaults (speed trap speed and lap)
                        modified_tuple = lap_tuple + (0.0, 0)
                        lap_entry = LapData(*modified_tuple)
                        packet.m_lapData.append(lap_entry)
                        logging.debug(f"Car {i}: Added LapData with {actual_tuple_len} fields + 2 defaults")
                    
                    elif actual_tuple_len == expected_fields - 2:
                        # If we're short 2 fields, add defaults for those
                        modified_tuple = lap_tuple + (0.0, 0.0, 0)
                        lap_entry = LapData(*modified_tuple)
                        packet.m_lapData.append(lap_entry)
                        logging.debug(f"Car {i}: Added LapData with {actual_tuple_len} fields + 3 defaults")
                    
                    else:
                        # Log but don't crash
                        logging.error(f"TUPLE LENGTH MISMATCH FOR CAR {i}! Expected ~{expected_fields}, Got {actual_tuple_len}. Skipping car.")
                        logging.debug(f"--> Problematic Tuple: {lap_tuple}") # Log the tuple if length is wrong
                        continue
                        
                except (TypeError, ValueError) as e:
                    logging.error(f"Error creating LapData for car {i}: {e}")
                    logging.debug(f"--> Problematic Tuple: {lap_tuple}")
                    continue

            except struct.error as e:
                logging.error(f"Failed to unpack LapData for car {i}: {e}")
                logging.error(f"--> Struct Error Details: Expected Size={expected_size}, Actual Slice Size={actual_size}, Format='{format_str}'")
                logging.debug(f"--> Hex Data attempted (Size {actual_size}): {current_chunk.hex()}")
                continue
            except TypeError as e: # Catch the specific error again
                logging.error(f"Caught TypeError creating LapData for car {i}: {e}")
                # Need actual_tuple_len from inside the try block if unpack succeeded but LapData failed
                # If unpack failed, this part won't be reached directly, but added for robustness
                current_tuple_len = 'N/A'
                current_tuple_val = 'N/A'
                if 'lap_tuple' in locals():
                    current_tuple_len = len(lap_tuple)
                    current_tuple_val = lap_tuple
                logging.error(f"--> TypeError Details: Attempted to unpack tuple of length {current_tuple_len} into LapData expecting 33 fields.")
                logging.debug(f"--> Problematic Tuple: {current_tuple_val}") # Log the tuple causing TypeError
                continue # Continue to the next car
            except Exception as e: # Catch any other unexpected errors
                logging.error(f"Unexpected error during LapData processing for car {i}: {e}", exc_info=True)
                continue
        return packet

# --- CarTelemetry Structures (F1 24 Spec Page 10) ---
@dataclass
class CarTelemetryData:
    m_speed: int                        # uint16
    m_throttle: float                   # float
    m_steer: float                      # float
    m_brake: float                      # float
    m_clutch: int                       # uint8
    m_gear: int                         # int8
    m_engineRPM: int                    # uint16
    m_drs: int                          # uint8
    m_revLightsPercent: int             # uint8
    m_revLightsBitValue: int            # uint16
    m_brakesTemperature: List[int]      # uint16[4]
    m_tyresSurfaceTemperature: List[int] # uint8[4]
    m_tyresInnerTemperature: List[int]  # uint8[4]
    m_engineTemperature: int            # uint16
    m_tyresPressure: List[float]        # float[4]
    m_surfaceType: List[int]            # uint8[4]

    # Format verified against F1 24 Spec Page 10
    TELEMETRY_DATA_FORMAT: str = "<HfffBbHBBH 4H 4B 4B H 4f 4B"
    SIZE: int = struct.calcsize(TELEMETRY_DATA_FORMAT)

@dataclass
class PacketCarTelemetry:
    m_header: PacketHeader
    m_carTelemetryData: List[CarTelemetryData] = field(default_factory=list)
    m_mfdPanelIndex: Optional[int] = None # uint8
    m_mfdPanelIndexSecondaryPlayer: Optional[int] = None # uint8
    m_suggestedGear: Optional[int] = None # int8

    PACKET_FORMAT: str = "" # Defined dynamically
    NUM_CARS = 22

    @classmethod
    def from_bytes(cls, header: PacketHeader, data: bytes) -> Optional['PacketCarTelemetry']:
        packet = cls(m_header=header)
        telemetry_data_size = CarTelemetryData.SIZE * cls.NUM_CARS

        if len(data) < telemetry_data_size:
             logging.warning(f"Telemetry packet too short for car data. Expected {telemetry_data_size}, got {len(data)}")
             return None

        telemetry_data_bytes = data[:telemetry_data_size]

        # Parse the car-specific data
        for i in range(cls.NUM_CARS):
            start = i * CarTelemetryData.SIZE
            end = start + CarTelemetryData.SIZE
            if end > len(telemetry_data_bytes):
                 logging.warning(f"Insufficient data for telemetry of car {i}")
                 break # Should not happen if initial length check passes
            try:
                telemetry_tuple = struct.unpack(CarTelemetryData.TELEMETRY_DATA_FORMAT, telemetry_data_bytes[start:end])
                # Map tuple elements to dataclass fields, handling arrays
                telemetry_entry = CarTelemetryData(
                     m_speed=telemetry_tuple[0],
                     m_throttle=telemetry_tuple[1],
                     m_steer=telemetry_tuple[2],
                     m_brake=telemetry_tuple[3],
                     m_clutch=telemetry_tuple[4],
                     m_gear=telemetry_tuple[5],
                     m_engineRPM=telemetry_tuple[6],
                     m_drs=telemetry_tuple[7],
                     m_revLightsPercent=telemetry_tuple[8],
                     m_revLightsBitValue=telemetry_tuple[9],
                     m_brakesTemperature=list(telemetry_tuple[10:14]), # Indices 10, 11, 12, 13
                     m_tyresSurfaceTemperature=list(telemetry_tuple[14:18]),# Indices 14, 15, 16, 17
                     m_tyresInnerTemperature=list(telemetry_tuple[18:22]),# Indices 18, 19, 20, 21
                     m_engineTemperature=telemetry_tuple[22],         # Index 22
                     m_tyresPressure=list(telemetry_tuple[23:27]),     # Indices 23, 24, 25, 26
                     m_surfaceType=list(telemetry_tuple[27:31])        # Indices 27, 28, 29, 30
                )
                packet.m_carTelemetryData.append(telemetry_entry)
            except struct.error as e:
                logging.error(f"Failed to unpack CarTelemetryData for car {i}: {e}")
                continue
            except IndexError as e:
                logging.error(f"Index error mapping CarTelemetryData fields for car {i}: {e}. Tuple length: {len(telemetry_tuple)}")
                continue

        # Parse the packet-level fields (MFD Index etc.) that follow the array
        extra_fields_offset = telemetry_data_size
        extra_fields_format = "<BBb" # mfdPanelIndex, mfdPanelIndexSecondaryPlayer, suggestedGear
        extra_fields_size = struct.calcsize(extra_fields_format)

        if len(data) >= extra_fields_offset + extra_fields_size:
            try:
                extra_tuple = struct.unpack(extra_fields_format, data[extra_fields_offset : extra_fields_offset + extra_fields_size])
                packet.m_mfdPanelIndex = extra_tuple[0]
                packet.m_mfdPanelIndexSecondaryPlayer = extra_tuple[1]
                packet.m_suggestedGear = extra_tuple[2]
            except struct.error as e:
                 logging.error(f"Failed to unpack extra fields in CarTelemetry packet: {e}")
        elif len(data) > telemetry_data_size:
             logging.warning(f"Telemetry packet has trailing data, but not enough for extra fields. Size: {len(data)}, Expected offset: {extra_fields_offset + extra_fields_size}")

        return packet

# --- CarStatus Structures (F1 24 Spec Pages 10-11) ---
@dataclass
class CarStatusData:
    m_tractionControl: int              # uint8
    m_antiLockBrakes: int               # uint8
    m_fuelMix: int                      # uint8 (0=lean, 1=std, 2=rich, 3=max)
    m_frontBrakeBias: int               # uint8 (%)
    m_pitLimiterStatus: int             # uint8 (0=off, 1=on)
    m_fuelInTank: float                 # float
    m_fuelCapacity: float               # float
    m_fuelRemainingLaps: float          # float
    m_maxRPM: int                       # uint16
    m_idleRPM: int                      # uint16
    m_maxGears: int                     # uint8
    m_drsAllowed: int                   # uint8 (0=not allowed, 1=allowed)
    m_drsActivationDistance: int        # uint16 (0=not available)
    m_actualTyreCompound: int           # uint8
    m_visualTyreCompound: int           # uint8
    m_tyresAgeLaps: int                 # uint8
    m_vehicleFiaFlags: int              # int8 (-1=invalid, 0=none, 1=green, 2=blue, 3=yellow)
    m_enginePowerICE: float             # float (W)
    m_enginePowerMGUK: float            # float (W)
    m_ersStoreEnergy: float             # float (Joules)
    m_ersDeployMode: int                # uint8 (0=None, 1=Medium, 2=Hotlap, 3=Overtake)
    m_ersHarvestedThisLapMGUK: float    # float
    m_ersHarvestedThisLapMGUH: float    # float
    m_ersDeployedThisLap: float         # float
    m_networkPaused: int                # uint8 (0=active, 1=paused)

    # FIX APPLIED: Corrected format string based on spec and test failures
    # Spec order: 5xB, 3xf, 2xH, 3xB, 1xH, 3xB, 1xb, 2xf, 1xf, 1xB, 3xf, 1xB = 27 items
    CAR_STATUS_FORMAT: str = "<BBBBB fff HH BBH BBB b ff f B fff B" # Strict spec order
    SIZE: int = struct.calcsize(CAR_STATUS_FORMAT) # Recalculate size


@dataclass
class PacketCarStatus:
    m_header: PacketHeader
    m_carStatusData: List[CarStatusData] = field(default_factory=list)

    NUM_CARS = 22

    @classmethod
    def from_bytes(cls, header: PacketHeader, data: bytes) -> Optional['PacketCarStatus']:
        packet = cls(m_header=header)
        expected_size = CarStatusData.SIZE * cls.NUM_CARS
        if len(data) < expected_size:
             logging.warning(f"CarStatus packet too short. Expected {expected_size}, got {len(data)}")
             return None

        for i in range(cls.NUM_CARS):
             start = i * CarStatusData.SIZE
             end = start + CarStatusData.SIZE
             if end > len(data):
                 logging.warning(f"Insufficient data for car status of car {i}")
                 break # Should not happen
             try:
                 status_tuple = struct.unpack(CarStatusData.CAR_STATUS_FORMAT, data[start:end])
                 status_entry = CarStatusData(*status_tuple) # Direct map
                 packet.m_carStatusData.append(status_entry)
             except struct.error as e:
                 logging.error(f"Failed to unpack CarStatusData for car {i}: {e}")
                 continue
             except IndexError as e:
                 logging.error(f"Index error mapping CarStatusData fields for car {i}: {e}. Check format/dataclass.")
                 continue
        return packet

# --- CarDamage Structures (F1 24 Spec Pages 12-13) ---
@dataclass
class CarDamageData:
    m_tyresWear: List[float]            # float[4] (RL, RR, FL, FR) %
    m_tyresDamage: List[int]            # uint8[4] (%)
    m_brakesDamage: List[int]           # uint8[4] (%)
    m_frontLeftWingDamage: int          # uint8 (%)
    m_frontRightWingDamage: int         # uint8 (%)
    m_rearWingDamage: int               # uint8 (%)
    m_floorDamage: int                  # uint8 (%)
    m_diffuserDamage: int               # uint8 (%)
    m_sidepodDamage: int                # uint8 (%)
    m_drsFault: int                     # uint8 (0=OK, 1=fault)
    m_ersFault: int                     # uint8 (0=OK, 1=fault)
    m_gearBoxDamage: int                # uint8 (%)
    m_engineDamage: int                 # uint8 (%)
    m_engineMGUHWear: int               # uint8 (%)
    m_engineESWear: int                 # uint8 (%)
    m_engineCEWear: int                 # uint8 (%)
    m_engineICEWear: int                # uint8 (%)
    m_engineMGUKWear: int               # uint8 (%)
    m_engineTCWear: int                 # uint8 (%)
    m_engineBlown: int                  # uint8 (0=OK, 1=fault)
    m_engineSeized: int                 # uint8 (0=OK, 1=fault)

    # Format verified against F1 24 Spec Pages 12-13
    CAR_DAMAGE_FORMAT: str = "<4f 4B 4B BBBBBB BB BBBBBBBB BB"
    SIZE: int = struct.calcsize(CAR_DAMAGE_FORMAT)

@dataclass
class PacketCarDamage:
    m_header: PacketHeader
    m_carDamageData: List[CarDamageData] = field(default_factory=list)

    NUM_CARS = 22

    @classmethod
    def from_bytes(cls, header: PacketHeader, data: bytes) -> Optional['PacketCarDamage']:
        packet = cls(m_header=header)
        expected_size = CarDamageData.SIZE * cls.NUM_CARS
        if len(data) < expected_size:
             logging.warning(f"CarDamage packet too short. Expected {expected_size}, got {len(data)}")
             return None

        for i in range(cls.NUM_CARS):
            start = i * CarDamageData.SIZE
            end = start + CarDamageData.SIZE
            if end > len(data):
                 logging.warning(f"Insufficient data for car damage of car {i}")
                 break # Should not happen
            try:
                damage_tuple = struct.unpack(CarDamageData.CAR_DAMAGE_FORMAT, data[start:end])
                # Map tuple elements, handling arrays
                damage_entry = CarDamageData(
                    m_tyresWear=list(damage_tuple[0:4]),         # Indices 0, 1, 2, 3
                    m_tyresDamage=list(damage_tuple[4:8]),       # Indices 4, 5, 6, 7
                    m_brakesDamage=list(damage_tuple[8:12]),      # Indices 8, 9, 10, 11
                    m_frontLeftWingDamage=damage_tuple[12],     # Index 12
                    m_frontRightWingDamage=damage_tuple[13],    # Index 13
                    m_rearWingDamage=damage_tuple[14],          # Index 14
                    m_floorDamage=damage_tuple[15],             # Index 15
                    m_diffuserDamage=damage_tuple[16],          # Index 16
                    m_sidepodDamage=damage_tuple[17],           # Index 17
                    m_drsFault=damage_tuple[18],                # Index 18
                    m_ersFault=damage_tuple[19],                # Index 19
                    m_gearBoxDamage=damage_tuple[20],           # Index 20
                    m_engineDamage=damage_tuple[21],            # Index 21
                    m_engineMGUHWear=damage_tuple[22],          # Index 22
                    m_engineESWear=damage_tuple[23],            # Index 23
                    m_engineCEWear=damage_tuple[24],            # Index 24
                    m_engineICEWear=damage_tuple[25],           # Index 25
                    m_engineMGUKWear=damage_tuple[26],          # Index 26
                    m_engineTCWear=damage_tuple[27],            # Index 27
                    m_engineBlown=damage_tuple[28],             # Index 28
                    m_engineSeized=damage_tuple[29]             # Index 29
                )
                packet.m_carDamageData.append(damage_entry)
            except struct.error as e:
                logging.error(f"Failed to unpack CarDamageData for car {i}: {e}")
                continue
            except IndexError as e:
                logging.error(f"Index error mapping CarDamageData fields for car {i}: {e}. Check format/dataclass. Tuple length: {len(damage_tuple)}")
                continue
        return packet

# --- Session Packet Structure (F1 24 Spec) ---
@dataclass
class PacketSessionData:
    m_header: PacketHeader
    m_weather: int = 0                      # uint8
    m_trackTemperature: int = 0             # int8
    m_airTemperature: int = 0               # int8
    m_totalLaps: int = 0                    # uint8
    m_trackLength: int = 0                  # uint16
    m_sessionType: int = 0                  # uint8
    m_trackId: int = -1                     # int8 (-1 for unknown)
    # Note: We only parse the fields we need for track detection
    
    @classmethod
    def from_bytes(cls, header: PacketHeader, data: bytes) -> Optional['PacketSessionData']:
        if len(data) < 8:  # Minimum bytes needed for trackId
            return None
        try:
            # Parse only the fields we need (up to trackId at offset 7)
            session_format = "<BbbBHBb"  # weather, trackTemp, airTemp, totalLaps, trackLength, sessionType, trackId
            unpacked = struct.unpack(session_format, data[:8])
            return cls(
                m_header=header,
                m_weather=unpacked[0],
                m_trackTemperature=unpacked[1],
                m_airTemperature=unpacked[2],
                m_totalLaps=unpacked[3],
                m_trackLength=unpacked[4],
                m_sessionType=unpacked[5],
                m_trackId=unpacked[6]
            )
        except struct.error as e:
            logging.error(f"Failed to unpack PacketSessionData: {e}")
            return None


# --- Tyre Compound Mapping (Example - Check F1 24 Spec Appendix) ---
# Based on F1 24 Spec Page 11 for m_actualTyreCompound
TYRE_COMPOUND_MAP = {
    # F1 Modern
    16: "C5", 17: "C4", 18: "C3", 19: "C2", 20: "C1", 21: "C0",
    7: "Inter", 8: "Wet",
    # F1 Classic (Add if needed)
    9: "Classic Dry", 10: "Classic Wet",
    # F2 (Add if needed)
    11: "F2 Super Soft", 12: "F2 Soft", 13: "F2 Medium", 14: "F2 Hard", 15: "F2 Wet",
}
DEFAULT_TYRE_COMPOUND = "Unknown"

# Map for m_visualTyreCompound (Page 11) - Use if needed for display only
VISUAL_TYRE_COMPOUND_MAP = {
     16: "Soft", 17: "Medium", 18: "Hard", 7: "Inter", 8: "Wet",
     # Add F2/Classic visual maps if needed
     # Map F2 visual compounds if using F2 cars often:
     # 19: "F2 Super Soft", 20: "F2 Soft", 21: "F2 Medium", 22: "F2 Hard", 15: "F2 Wet",
}
DEFAULT_VISUAL_TYRE_COMPOUND = "Unknown Visual"

# ERS Deploy Mode Mapping (F1 24 Spec Page 11)
ERS_DEPLOY_MODE_MAP = {
    0: "None", 1: "Medium", 2: "Hotlap", 3: "Overtake",
}
DEFAULT_ERS_MODE = "N/A"

# Track ID Mapping (F1 24 Spec Appendix)
TRACK_ID_MAP = {
    0: "Melbourne", 1: "Paul Ricard", 2: "Shanghai", 3: "Sakhir (Bahrain)", 4: "Catalunya",
    5: "Monaco", 6: "Montreal", 7: "Silverstone", 8: "Hockenheim", 9: "Hungaroring",
    10: "Spa", 11: "Monza", 12: "Singapore", 13: "Suzuka", 14: "Abu Dhabi",
    15: "Texas", 16: "Brazil", 17: "Austria", 18: "Sochi", 19: "Mexico",
    20: "Baku (Azerbaijan)", 21: "Sakhir Short", 22: "Silverstone Short", 23: "Texas Short",
    24: "Suzuka Short", 25: "Hanoi", 26: "Zandvoort", 27: "Imola", 28: "Portimão",
    29: "Jeddah", 30: "Miami", 31: "Las Vegas", 32: "Losail"
}
DEFAULT_TRACK_NAME = "Unknown Track"


# --- Telemetry Bridge Class ---
class TelemetryBridge:
    """Receives F1 telemetry data via UDP and sends aggregated data to a web endpoint."""
    
    # Number of cars to track (same as in the packet classes)
    NUM_CARS = 22

    def __init__(self, driver: str, track: str, url: str, ip: str, port: int, debug: bool, auto_detect_track: bool = True, datacloud: bool = False):
        self.driver_name: str = driver
        self.track_name: str = track
        self.original_track_name: str = track  # Store original for fallback
        self.auto_detect_track: bool = auto_detect_track
        self.datacloud_enabled: bool = datacloud
        self.api_url: str = url
        self.udp_ip: str = ip
        self.udp_port: int = port
        self.debug_mode: bool = debug
        self.session_id: str = str(uuid.uuid4())

        self.sock: Optional[socket.socket] = None
        self.executor: concurrent.futures.ThreadPoolExecutor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        self.start_time: float = time.time()
        self.last_status_update_time: float = self.start_time
        self.last_send_time: float = self.start_time
        self.packets_received: int = 0
        self.player_car_index: int = -1 # Determined from header
        
        # Performance optimization tracking
        if PERFORMANCE_MODE:
            self._last_debug_log: float = 0.0
            self._log_counter: int = 0
            self._status_log_counter: int = 0
            self._async_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="HTTP-Async")

        # State Data
        self.latest_lap_data: Optional[LapData] = None
        self.latest_telemetry: Optional[CarTelemetryData] = None
        self.latest_car_status: Optional[CarStatusData] = None
        self.latest_car_damage: Optional[CarDamageData] = None # Added state for damage
        self.latest_event: Optional[Dict[str, Any]] = None  # Store the latest event
        self.latest_header: Optional[PacketHeader] = None  # Store latest packet header for frame ID

        self.current_lap_num: int = 0
        self.lap_just_completed: bool = False
        self.last_lap_time_ms: int = 0

        # Aggregation State
        self.aggregated_data: Dict[str, Dict[str, Any]] = self._init_aggregation()
        self.lap_start_time: Optional[float] = None
        
        # Data Cloud Integration
        self.datacloud_client = None
        if self.datacloud_enabled:
            try:
                load_dotenv()
                sf_client_id = os.environ.get("SF_CLIENT_ID", "")
                sf_private_key_path = os.environ.get("SF_PRIVATE_KEY_PATH", "")
                sf_username = os.environ.get("SF_USERNAME", "")
                salesforce_domain = os.environ.get("SALESFORCE_DOMAIN", "")
                
                if sf_client_id and sf_private_key_path and sf_username and salesforce_domain:
                    self.datacloud_client = create_datacloud_client(
                        salesforce_domain=salesforce_domain,
                        client_id=sf_client_id,
                        private_key_path=sf_private_key_path,
                        username=sf_username,
                        debug=self.debug_mode
                    )
                    print("✅ Data Cloud client initialized successfully")
                else:
                    print("❌ Data Cloud integration enabled but missing configuration in .env file")
                    self.datacloud_enabled = False
            except Exception as e:
                print(f"❌ Failed to initialize Data Cloud client: {e}")
                self.datacloud_enabled = False

        # Connection State
        self.connection_stats: Dict[str, float] = {"total_sent": 0, "total_failed": 0, "total_response_time": 0}
        self.send_retries: int = 0
        self.current_send_interval: float = DEFAULT_SEND_INTERVAL_S

        self._setup_logging()
        logging.info(f"Initializing {APP_NAME}")
        if self.auto_detect_track:
            logging.info(f"Driver: {self.driver_name}, Track: {self.track_name} (auto-detection enabled), Session: {self.session_id}")
        else:
            logging.info(f"Driver: {self.driver_name}, Track: {self.track_name} (fixed), Session: {self.session_id}")
        logging.info(f"API Endpoint: {self.api_url}")
        logging.info(f"Listening on UDP {self.udp_ip}:{self.udp_port}")

    def _setup_logging(self):
        log_level = logging.DEBUG if self.debug_mode else logging.INFO
        logging.basicConfig(level=log_level,
                            format='%(asctime)s [%(levelname)-8s] %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

    def _init_aggregation(self) -> Dict[str, Dict[str, Any]]:
        # Reset max values as well
        return {
            "speed": {"values": [], "max": 0},
            "throttle": {"values": [], "max": 0.0},
            "brake": {"values": [], "max": 0.0},
            "rpm": {"values": [], "max": 0},
            "gear": {"values": [], "max": 0}
        }

    def _reset_lap_aggregates(self):
        logging.debug("Resetting lap aggregation data.")
        self.aggregated_data = self._init_aggregation()
        self.lap_start_time = time.time()

    def _update_aggregation(self, telemetry: CarTelemetryData):
        if not telemetry: return
        agg = self.aggregated_data
        agg["speed"]["values"].append(telemetry.m_speed)
        agg["speed"]["max"] = max(agg["speed"]["max"], telemetry.m_speed)
        # ... (rest of aggregation logic remains the same) ...
        agg["throttle"]["values"].append(telemetry.m_throttle)
        agg["throttle"]["max"] = max(agg["throttle"]["max"], telemetry.m_throttle)
        agg["brake"]["values"].append(telemetry.m_brake)
        agg["brake"]["max"] = max(agg["brake"]["max"], telemetry.m_brake)
        agg["rpm"]["values"].append(telemetry.m_engineRPM)
        agg["rpm"]["max"] = max(agg["rpm"]["max"], telemetry.m_engineRPM)
        if telemetry.m_gear > 0:
            agg["gear"]["values"].append(telemetry.m_gear)
            agg["gear"]["max"] = max(agg["gear"]["max"], telemetry.m_gear)
        elif telemetry.m_gear != -1:
             agg["gear"]["values"].append(telemetry.m_gear)


    def _calculate_lap_stats(self) -> Dict[str, Dict[str, Any]]:
        # (Calculation logic remains the same)
        stats = {}
        for key, data in self.aggregated_data.items():
            if data["values"]:
                if key == "gear":
                    gear_counts = {}
                    for g in data["values"]:
                        gear_counts[g] = gear_counts.get(g, 0) + 1
                    most_used = max(gear_counts, key=gear_counts.get) if gear_counts else 0
                    stats[key] = {"mostUsed": most_used, "max": data["max"]}
                elif key in ["speed", "rpm"]:
                    avg = round(sum(data["values"]) / len(data["values"]))
                    stats[key] = {"average": avg, "max": data["max"]}
                else:
                    avg = sum(data["values"]) / len(data["values"])
                    stats[key] = {"average": avg, "max": data["max"]}
            else:
                stats[key] = {"average": 0 if key != "gear" else None, "mostUsed": 0 if key == "gear" else None, "max": data["max"]}
        return stats

    # --- Packet Handlers ---

    def _handle_lap_data(self, packet: PacketLapData):
        if not packet or not packet.m_lapData or self.player_car_index == -1 or self.player_car_index >= len(packet.m_lapData):
            return
        player_lap = packet.m_lapData[self.player_car_index]

        # Check for lap completion *before* updating self.latest_lap_data
        if player_lap.m_currentLapNum > self.current_lap_num and self.current_lap_num > 0: # Avoid triggering on first lap
            logging.info(f"Lap {self.current_lap_num} completed. New lap: {player_lap.m_currentLapNum}")
            self.lap_just_completed = True
            # Use lastLapTimeInMS from the *new* packet for the completed lap
            self.last_lap_time_ms = player_lap.m_lastLapTimeInMS

        self.current_lap_num = player_lap.m_currentLapNum
        self.latest_lap_data = player_lap # Update state *after* checking completion

    def _handle_telemetry(self, packet: PacketCarTelemetry):
        if not packet or not packet.m_carTelemetryData or self.player_car_index == -1 or self.player_car_index >= len(packet.m_carTelemetryData):
            return
        player_telemetry = packet.m_carTelemetryData[self.player_car_index]
        self.latest_telemetry = player_telemetry
        self._update_aggregation(player_telemetry)
        # (Logging logic remains the same)
        if self.debug_mode and self.packets_received % 20 == 0:
             gear_str = f"G:{player_telemetry.m_gear}"
             rpm_str = f"RPM:{player_telemetry.m_engineRPM:<5}"
             drs_str = "DRS" if player_telemetry.m_drs == 1 else ""
             logging.debug(f"TELEMETRY: {player_telemetry.m_speed:>3}kmh | "
                           f"T:{player_telemetry.m_throttle*100:3.0f}% | "
                           f"B:{player_telemetry.m_brake*100:3.0f}% | "
                           f"{gear_str:<4} | {rpm_str} | {drs_str}")


    def _handle_car_status(self, packet: PacketCarStatus):
        if not packet or not packet.m_carStatusData or self.player_car_index == -1 or self.player_car_index >= len(packet.m_carStatusData):
            return
        self.latest_car_status = packet.m_carStatusData[self.player_car_index]
        # (Logging logic remains the same, uses correct fields)
        if self.debug_mode and self.packets_received % 50 == 0:
            tyre_idx = self.latest_car_status.m_visualTyreCompound # Use visual for display usually
            # Use VISUAL_TYRE_COMPOUND_MAP here for display consistency
            tyre = VISUAL_TYRE_COMPOUND_MAP.get(tyre_idx, DEFAULT_VISUAL_TYRE_COMPOUND)
            ers_joules = self.latest_car_status.m_ersStoreEnergy
            ers_max_joules = 4000000 # Constant for F1 cars
            ers_perc = (ers_joules / ers_max_joules * 100) if ers_max_joules > 0 else 0 # Avoid division by zero
            logging.debug(f"STATUS: Tyre:{tyre}, Fuel:{self.latest_car_status.m_fuelInTank:.1f}kg, "
                          f"ERS:{ers_perc:.0f}% ({ers_joules:.0f}J) "
                          f"DRS Allowed: {self.latest_car_status.m_drsAllowed}")


    def _handle_event(self, header: PacketHeader, data: bytes):
        """Handles incoming Event packets with special handling for important events."""
        if len(data) < 4:
            return
            
        try:
            event_code = data[:4].decode('utf-8', errors='ignore')
            
            # Map event codes to descriptive messages - skip unimportant events
            event_descriptions = {
                'SSTA': '🏁 Session Started',
                'SEND': '🏁 Session Ended',
                'FTLP': '⚡ Fastest Lap',
                'RTMT': '❌ Driver Retirement',
                'DRSE': '🟢 DRS Enabled by Race Control',
                'DRSD': '🔴 DRS Disabled by Race Control',
                'TMPT': '🔧 Team mate in pits',
                'CHQF': '🏁 Chequered flag waved',
                'RCWN': '🏆 Race Winner announced',
                'PENA': '⚠️ Penalty Issued',
                'SPTP': '📊 Speed Trap triggered',
                'STLG': '🔴 Start lights',
                'LGOT': '🟢 Lights out - Race start!',
                'DTSV': '⚠️ Drive through penalty served',
                'SGSV': '⚠️ Stop & Go penalty served',
                'FLBK': '⏪ Flashback activated',
                # 'BUTN': '🎮 Button status changed', # Removed - too noisy
                'RDFL': '🔴 RED FLAG shown',
                'OVTK': '⏩ Overtake occurred',
                'SCAR': '🚨 Safety Car deployed',
                'COLL': '💥 Collision detected'
            }
            
            # Skip processing BUTN events completely
            if event_code == 'BUTN':
                return
                
            # Get the human-readable description or use the code if not found
            base_description = event_descriptions.get(event_code, f'Event: {event_code}')
            
            # Enhanced detail description
            detailed_description = base_description
            event_data = {}
            
            # Special handling for specific events with more details
            if event_code == 'SSTA':
                # Session started - COMPLETELY reset all state
                logging.info("🏁 New session started - resetting all telemetry data")
                self._reset_lap_aggregates()
                self.current_lap_num = 0
                self.last_lap_time_ms = 0
                self.lap_just_completed = False
                
                # Clear all cached telemetry data to ensure clean state
                self.latest_lap_data = None
                self.latest_telemetry = None
                self.latest_car_status = None
                self.latest_car_damage = None
                
            elif event_code == 'SEND':
                # Session ended
                logging.info("🏁 Session ended - finalizing telemetry")
                
            elif event_code == 'FTLP':
                # Try to parse fastest lap details if available
                if len(data) >= 8:  # Ensure we have enough data for vehicle index + lap time
                    try:
                        # Extract vehicle index and lap time
                        vehicle_idx = data[4]
                        # Unpack the lap time as a float (4 bytes starting at position 5)
                        lap_time_bytes = data[5:9]
                        if len(lap_time_bytes) == 4:
                            lap_time = struct.unpack('<f', lap_time_bytes)[0]
                            lap_time_str = f"{lap_time:.3f}s"
                            
                            # Store for payload
                            event_data['lapTime'] = lap_time
                            event_data['vehicleIdx'] = vehicle_idx
                            
                            if vehicle_idx == header.m_playerCarIndex:
                                detailed_description = f"⚡ YOU just set the FASTEST LAP of the session! ({lap_time_str})"
                                logging.info(detailed_description)
                            else:
                                detailed_description = f"⚡ Car #{vehicle_idx} set the fastest lap of the session: {lap_time_str}"
                                logging.info(detailed_description)
                        else:
                            logging.debug(f"Insufficient data for lap time unpacking: {len(lap_time_bytes)} bytes")
                    except Exception as e:
                        logging.debug(f"Error parsing FTLP event details: {e}")
                        
            elif event_code == 'PENA':
                # Try to extract penalty details
                if len(data) >= 11:  # Need at least 7 bytes after the event code
                    try:
                        penalty_type = data[4]
                        infringement_type = data[5]
                        vehicle_idx = data[6]
                        other_vehicle_idx = data[7]
                        
                        # Define penalty type names
                        penalty_types = {
                            0: "Drive through", 1: "Stop & Go", 2: "Grid penalty", 
                            3: "Penalty reminder", 4: "Time penalty", 5: "Warning",
                            6: "Disqualified", 7: "Removed from formation lap",
                            8: "Parked too long timer", 9: "Tyre regulations",
                            10: "This lap invalidated", 11: "This and next lap invalidated",
                            12: "This lap invalidated without reason", 13: "This and next lap invalidated without reason",
                            14: "This and previous lap invalidated", 15: "This and previous lap invalidated without reason",
                            16: "Retired", 17: "Black flag timer"
                        }
                        
                        # Define infringement type names
                        infringement_types = {
                            0: "Blocking by slow driving", 1: "Blocking by wrong way driving",
                            2: "Reversing off the start line", 3: "Big Collision",
                            4: "Small Collision", 5: "Collision failed to hand back position single",
                            6: "Collision failed to hand back position multiple", 7: "Corner cutting gained time",
                            8: "Corner cutting overtake single", 9: "Corner cutting overtake multiple",
                            10: "Crossed pit exit lane", 11: "Ignoring blue flags",
                            12: "Ignoring yellow flags", 13: "Ignoring drive through",
                            14: "Too many drive throughs", 15: "Drive through reminder serve within n laps",
                            16: "Drive through reminder serve this lap", 17: "Pit lane speeding",
                            18: "Parked for too long", 19: "Ignoring tyre regulations",
                            20: "Too many penalties", 21: "Multiple warnings",
                            22: "Approaching disqualification", 23: "Tyre regulations select single",
                            24: "Tyre regulations select multiple", 25: "Lap invalidated corner cutting",
                            26: "Lap invalidated running wide", 27: "Corner cutting ran wide gained time minor",
                            28: "Corner cutting ran wide gained time significant", 29: "Corner cutting ran wide gained time extreme",
                            30: "Lap invalidated wall riding", 31: "Lap invalidated flashback used",
                            32: "Lap invalidated reset to track", 33: "Blocking the pitlane",
                            34: "Jump start", 35: "Safety car to car collision",
                            36: "Safety car illegal overtake", 37: "Safety car exceeding allowed pace",
                            38: "Virtual safety car exceeding allowed pace", 39: "Formation lap below allowed speed",
                            40: "Formation lap parking"
                        }
                        
                        # Get penalty and infringement descriptions
                        penalty_desc = penalty_types.get(penalty_type, f"Unknown penalty ({penalty_type})")
                        infringement_desc = infringement_types.get(infringement_type, f"Unknown infringement ({infringement_type})")
                        
                        # Store for payload
                        event_data['penaltyType'] = penalty_type
                        event_data['infringementType'] = infringement_type
                        event_data['vehicleIdx'] = vehicle_idx
                        event_data['otherVehicleIdx'] = other_vehicle_idx
                        
                        # Create detailed description
                        if vehicle_idx == header.m_playerCarIndex:
                            detailed_description = f"⚠️ YOU received a {penalty_desc} penalty for {infringement_desc}"
                        else:
                            detailed_description = f"⚠️ Car #{vehicle_idx} received a {penalty_desc} penalty for {infringement_desc}"
                            
                        if other_vehicle_idx != 255 and infringement_type in [3, 4, 5, 6]:  # Collision penalties
                            detailed_description += f" with Car #{other_vehicle_idx}"
                            
                        logging.info(detailed_description)
                    except Exception as e:
                        logging.debug(f"Error parsing PENA event details: {e}")
                        
            elif event_code == 'OVTK':
                # Try to extract overtake details
                if len(data) >= 6:  # Need at least 2 bytes after the event code
                    try:
                        overtaking_idx = data[4]
                        overtaken_idx = data[5]
                        
                        # Store for payload
                        event_data['overtakingVehicleIdx'] = overtaking_idx
                        event_data['overtakenVehicleIdx'] = overtaken_idx
                        
                        # Create detailed description
                        if overtaking_idx == header.m_playerCarIndex:
                            detailed_description = f"⏩ YOU overtook Car #{overtaken_idx}!"
                        elif overtaken_idx == header.m_playerCarIndex:
                            detailed_description = f"⏩ Car #{overtaking_idx} overtook YOU!"
                        else:
                            detailed_description = f"⏩ Car #{overtaking_idx} overtook Car #{overtaken_idx}"
                            
                        logging.info(detailed_description)
                    except Exception as e:
                        logging.debug(f"Error parsing OVTK event details: {e}")
                        
            elif event_code == 'COLL':
                # Try to extract collision details
                if len(data) >= 6:  # Need at least 2 bytes after the event code
                    try:
                        vehicle1_idx = data[4]
                        vehicle2_idx = data[5]
                        
                        # Store for payload
                        event_data['vehicle1Idx'] = vehicle1_idx
                        event_data['vehicle2Idx'] = vehicle2_idx
                        
                        # Create detailed description
                        if vehicle1_idx == header.m_playerCarIndex:
                            detailed_description = f"💥 YOU collided with Car #{vehicle2_idx}!"
                        elif vehicle2_idx == header.m_playerCarIndex:
                            detailed_description = f"💥 Car #{vehicle1_idx} collided with YOU!"
                        else:
                            detailed_description = f"💥 Car #{vehicle1_idx} collided with Car #{vehicle2_idx}"
                            
                        logging.info(detailed_description)
                    except Exception as e:
                        logging.debug(f"Error parsing COLL event details: {e}")
            else:
                # Log the basic event
                logging.info(f"EVENT: {base_description}")
            
            # Skip sending BUTN events entirely
            if event_code != 'BUTN':
                # Include the event in the next telemetry payload with enhanced data
                event_payload = {
                    'code': event_code,
                    'description': detailed_description,
                    'timestamp': datetime.datetime.now().isoformat(),
                    'data': event_data  # Include the parsed event data
                }
                
                # Store the event for inclusion in the next payload
                self.latest_event = event_payload
                
        except Exception as e:
            logging.warning(f"Error processing event packet: {e}")

    def _handle_damage(self, packet: PacketCarDamage): # Changed signature to accept parsed packet
        """Handles incoming Car Damage packet."""
        if not packet or not packet.m_carDamageData or self.player_car_index == -1 or self.player_car_index >= len(packet.m_carDamageData):
             return
        self.latest_car_damage = packet.m_carDamageData[self.player_car_index]

        if self.debug_mode and self.packets_received % 30 == 0: # Log damage periodically
            dmg = self.latest_car_damage
            logging.debug(f"DAMAGE: Wing(FL:{dmg.m_frontLeftWingDamage} FR:{dmg.m_frontRightWingDamage} R:{dmg.m_rearWingDamage}) "
                          f"TyreWear(FL:{dmg.m_tyresWear[2]:.1f} FR:{dmg.m_tyresWear[3]:.1f} RL:{dmg.m_tyresWear[0]:.1f} RR:{dmg.m_tyresWear[1]:.1f})% "
                          f"Eng:{dmg.m_engineDamage}% Gearbox:{dmg.m_gearBoxDamage}% DRSFault:{dmg.m_drsFault}")

    def _handle_session(self, packet: PacketSessionData):
        """Handles incoming Session packet for track detection."""
        if not packet:
            return
        
        # Auto-detect track name from session data
        if self.auto_detect_track and packet.m_trackId != -1:
            detected_track = TRACK_ID_MAP.get(packet.m_trackId, DEFAULT_TRACK_NAME)
            if detected_track != DEFAULT_TRACK_NAME and detected_track != self.track_name:
                old_track = self.track_name
                self.track_name = detected_track
                logging.info(f"🏁 Track auto-detected: {detected_track} (was: {old_track})")
        
        if self.debug_mode and self.packets_received % 100 == 0:
            logging.debug(f"SESSION: Track ID={packet.m_trackId}, Track={self.track_name}, "
                         f"Weather={packet.m_weather}, TrackTemp={packet.m_trackTemperature}°C, "
                         f"TotalLaps={packet.m_totalLaps}")


    # --- Network and Sending ---

    def _prepare_payload(self, header: Optional[PacketHeader] = None) -> Optional[Dict[str, Any]]:
        """Constructs the JSON payload to send to the API."""
        # Always send a payload with whatever data we have - don't require complete data
        # This ensures dashboard gets updates even when some packet types are missing

        # Calculate stats just before sending
        lap_stats = self._calculate_lap_stats()

        now_iso = datetime.datetime.utcnow().isoformat() + "Z"
        
        # Send minimal payload if no data available yet
        if not self.latest_telemetry and not self.latest_lap_data:
            logging.debug(f"Sending minimal payload - no telemetry or lap data available yet. "
                         f"latest_telemetry={self.latest_telemetry is not None}, "
                         f"latest_lap_data={self.latest_lap_data is not None}, "
                         f"player_car_index={self.player_car_index}")
            return {
                "timestamp": now_iso,
                "sessionId": self.session_id,
                "driverName": self.driver_name,
                "track": self.track_name,
                "connectionStatus": "waiting_for_data"
            }
        
        logging.debug(f"Preparing full payload with telemetry={self.latest_telemetry is not None}, "
                     f"lap_data={self.latest_lap_data is not None}")
        is_lap_complete = self.lap_just_completed
        final_lap_time_sec = (self.last_lap_time_ms / 1000.0) if is_lap_complete and self.last_lap_time_ms > 0 else None

        # Extract current values safely
        current_telemetry = self.latest_telemetry
        current_lap = self.latest_lap_data
        current_status = self.latest_car_status
        current_damage = self.latest_car_damage

        # Map tyre and ERS mode indices to strings
        tyre_compound_str = TYRE_COMPOUND_MAP.get(current_status.m_actualTyreCompound, DEFAULT_TYRE_COMPOUND)
        ers_mode_str = ERS_DEPLOY_MODE_MAP.get(current_status.m_ersDeployMode, DEFAULT_ERS_MODE)

        # Format tyre wear from CarDamageData (Indices: 0=RL, 1=RR, 2=FL, 3=FR)
        tyre_wear_payload = {
            "frontLeft": current_damage.m_tyresWear[2] / 100.0 if len(current_damage.m_tyresWear) > 2 and current_damage.m_tyresWear[2] is not None else None,
            "frontRight": current_damage.m_tyresWear[3] / 100.0 if len(current_damage.m_tyresWear) > 3 and current_damage.m_tyresWear[3] is not None else None,
            "rearLeft": current_damage.m_tyresWear[0] / 100.0 if len(current_damage.m_tyresWear) > 0 and current_damage.m_tyresWear[0] is not None else None,
            "rearRight": current_damage.m_tyresWear[1] / 100.0 if len(current_damage.m_tyresWear) > 1 and current_damage.m_tyresWear[1] is not None else None,
        }

        # Add brake temp from CarTelemetryData (Indices: 0=RL, 1=RR, 2=FL, 3=FR)
        brake_temp_payload = {
            "frontLeft": current_telemetry.m_brakesTemperature[2] if len(current_telemetry.m_brakesTemperature) > 2 else None,
            "frontRight": current_telemetry.m_brakesTemperature[3] if len(current_telemetry.m_brakesTemperature) > 3 else None,
            "rearLeft": current_telemetry.m_brakesTemperature[0] if len(current_telemetry.m_brakesTemperature) > 0 else None,
            "rearRight": current_telemetry.m_brakesTemperature[1] if len(current_telemetry.m_brakesTemperature) > 1 else None,
        }

        # Generate primary keys for Data Cloud
        frame_id = header.m_frameIdentifier if header else int(time.time()*1000)
        telemetry_id = f"{self.session_id}-{frame_id}-{int(time.time()*1000)}"
        
        # Apply reasonable bounds checking for lap times
        # F1 lap times should be between 0 and 10 minutes (600 seconds = 600,000 ms)
        current_lap_time_ms = current_lap.m_currentLapTimeInMS
        last_lap_time_ms = self.last_lap_time_ms if is_lap_complete else None
        
        # Validate current lap time (0 to 600 seconds)
        if current_lap_time_ms > 600000:  # More than 10 minutes
            logging.warning(f"Invalid current lap time received: {current_lap_time_ms}ms ({current_lap_time_ms/1000.0:.3f}s)")
            current_lap_time_seconds = 0  # Reset to 0 if invalid
        else:
            current_lap_time_seconds = current_lap_time_ms / 1000.0
        
        # Validate last lap time (0 to 600 seconds)  
        if last_lap_time_ms and last_lap_time_ms > 600000:  # More than 10 minutes
            logging.warning(f"Invalid last lap time received: {last_lap_time_ms}ms ({last_lap_time_ms/1000.0:.3f}s)")
            final_lap_time_sec = None  # Reset to None if invalid
        else:
            final_lap_time_sec = last_lap_time_ms / 1000.0 if last_lap_time_ms else None

        # Construct the main payload dictionary with all essential data
        payload = {
            "telemetryId": telemetry_id,  # Primary key for Data Cloud
            "timestamp": now_iso,
            "sessionId": self.session_id,
            "driverName": self.driver_name,
            "track": self.track_name,
            # Validate lap number (should be reasonable, 1-200 for any F1 session)
            "lapNumber": self.current_lap_num if 1 <= self.current_lap_num <= 200 else 1,
            
            "lapTimeSoFar": current_lap_time_seconds,
            "lastLapTime": final_lap_time_sec,
            "lapCompleted": is_lap_complete,
            # Validate sector (should be 0, 1, or 2 from UDP, displayed as 1, 2, 3)
            "sector": (current_lap.m_sector + 1) if current_lap.m_sector in [0, 1, 2] else 1,
            # Validate position (should be 1-22 for F1)
            "position": current_lap.m_carPosition if 1 <= current_lap.m_carPosition <= 22 else 1,
            "speed": {
                "current": current_telemetry.m_speed,
                "average": lap_stats.get("speed", {}).get("average"),
                "max": lap_stats.get("speed", {}).get("max", 0)
            },
            "throttle": {
                "current": current_telemetry.m_throttle,
                "average": lap_stats.get("throttle", {}).get("average"),
                "max": lap_stats.get("throttle", {}).get("max", 0.0)
            },
            "brake": {
                "current": current_telemetry.m_brake,
                "average": lap_stats.get("brake", {}).get("average"),
                "max": lap_stats.get("brake", {}).get("max", 0.0)
            },
            # Add steering data explicitly for steering wheel display
            "steer": {
                "current": current_telemetry.m_steer if hasattr(current_telemetry, 'm_steer') else 0.0,
                "average": 0.0, # We don't track average steering
            },
            "gear": {
                "current": current_telemetry.m_gear,
                "mostUsed": lap_stats.get("gear", {}).get("mostUsed"),
                "max": lap_stats.get("gear", {}).get("max", 0)
            },
            "engineRPM": {
                "current": current_telemetry.m_engineRPM,
                "average": lap_stats.get("rpm", {}).get("average"),
                "max": lap_stats.get("rpm", {}).get("max", 0)
            },
            "drsActive": current_telemetry.m_drs == 1,
            
            # Basic race and car status
            "lapValid": current_lap.m_currentLapInvalid == 0,
            "pitStatus": current_lap.m_pitStatus, # For pit detection
            
            # Add event information if available
            "event": self.latest_event,
        }
        
        # Add optional data if available - status data
        if self.latest_car_status:
            current_status = self.latest_car_status
            ers_mode_str = ERS_DEPLOY_MODE_MAP.get(current_status.m_ersDeployMode, DEFAULT_ERS_MODE)
            tyre_compound_str = TYRE_COMPOUND_MAP.get(current_status.m_actualTyreCompound, DEFAULT_TYRE_COMPOUND)
            
            # Add car status data
            payload.update({
                "drsAllowed": current_status.m_drsAllowed,
                "ersDeployMode": ers_mode_str,
                "ersStoreEnergy": current_status.m_ersStoreEnergy,
                "tyreCompound": tyre_compound_str,
                "fuelInTank": current_status.m_fuelInTank,
                "fuelRemainingLaps": current_status.m_fuelRemainingLaps if hasattr(current_status, 'm_fuelRemainingLaps') else 0,
                "vehicleFiaFlags": current_status.m_vehicleFiaFlags, # For flag status
            })
        
        # Add optional data - damage and temperatures
        if self.latest_car_damage and self.latest_telemetry:
            current_damage = self.latest_car_damage
            
            # Extract tyre wear data
            tyre_wear_payload = {
                "frontLeft": current_damage.m_tyresWear[2] / 100.0 if len(current_damage.m_tyresWear) > 2 else 0.0,
                "frontRight": current_damage.m_tyresWear[3] / 100.0 if len(current_damage.m_tyresWear) > 3 else 0.0,
                "rearLeft": current_damage.m_tyresWear[0] / 100.0 if len(current_damage.m_tyresWear) > 0 else 0.0,
                "rearRight": current_damage.m_tyresWear[1] / 100.0 if len(current_damage.m_tyresWear) > 1 else 0.0,
            }
            
            # Extract brake temps
            brake_temp_payload = {
                "frontLeft": current_telemetry.m_brakesTemperature[2] if len(current_telemetry.m_brakesTemperature) > 2 else 0,
                "frontRight": current_telemetry.m_brakesTemperature[3] if len(current_telemetry.m_brakesTemperature) > 3 else 0,
                "rearLeft": current_telemetry.m_brakesTemperature[0] if len(current_telemetry.m_brakesTemperature) > 0 else 0,
                "rearRight": current_telemetry.m_brakesTemperature[1] if len(current_telemetry.m_brakesTemperature) > 1 else 0,
            }
            
            payload.update({
                "tyreWear": tyre_wear_payload,
                "brakeTemperature": brake_temp_payload,
                "damage": {
                    "frontLeftWing": current_damage.m_frontLeftWingDamage,
                    "frontRightWing": current_damage.m_frontRightWingDamage,
                    "rearWing": current_damage.m_rearWingDamage,
                    "floor": current_damage.m_floorDamage,
                    "diffuser": current_damage.m_diffuserDamage,
                    "sidepod": current_damage.m_sidepodDamage,
                    "gearBox": current_damage.m_gearBoxDamage,
                    "engine": current_damage.m_engineDamage,
                    "drsFault": current_damage.m_drsFault == 1,
                    "ersFault": current_damage.m_ersFault == 1,
                }
            })
            
        # Clear the event after including it in a payload
        self.latest_event = None
        
        return payload

    def _send_payload(self, header: Optional[PacketHeader] = None):
        """Prepares and sends the telemetry payload to the API endpoint."""
        payload = self._prepare_payload(header)
        if not payload:
            return

        # Log essential info only in debug mode and with throttling
        if self.debug_mode:
            self._debug_log_throttled(f"📤 Sending Payload: Lap {payload.get('lapNumber', '?')}-S{payload.get('sector', '?')}, "
                         f"Speed:{payload.get('speed', {}).get('current', '?')}kmh")
            
            # Only log full payload occasionally to reduce overhead
            if PERFORMANCE_MODE and hasattr(self, '_log_counter') and self._log_counter % 50 == 0:
                try:
                    self._debug_log_throttled(f"Full payload:\n{json.dumps(payload, indent=2)}", force=True)
                except TypeError as e:
                    logging.error(f"Payload contains non-serializable data: {e}")

        # Use async sending if performance mode is enabled
        if PERFORMANCE_MODE and hasattr(self, '_async_executor'):
            self._send_http_async(payload)
        else:
            self._send_http_sync(payload)

    def _send_http_async(self, payload: Dict[str, Any]):
        """Send HTTP request asynchronously to prevent blocking UDP processing"""
        future = self._async_executor.submit(self._send_http_sync, payload)
        future.add_done_callback(self._handle_async_send_result)

    def _handle_async_send_result(self, future):
        """Handle the result of async HTTP send"""
        try:
            future.result()  # This will raise any exception that occurred
        except Exception as e:
            logging.error(f"Async HTTP send failed: {e}")

    def _send_http_sync(self, payload: Dict[str, Any]):
        """Synchronous HTTP send implementation"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': f'{APP_NAME}/1.0',
            'Accept': 'application/json'
        }
        start_req_time = time.monotonic()

        try:
            with requests.Session() as session:
                response = session.post(self.api_url, json=payload, headers=headers, timeout=10.0)
            elapsed_ms = (time.monotonic() - start_req_time) * 1000

            self.connection_stats["total_sent"] += 1
            self.connection_stats["total_response_time"] += elapsed_ms

            if 200 <= response.status_code < 300:
                # Only log successful sends in debug mode with throttling
                if self.debug_mode:
                    self._debug_log_throttled(f"✅ Send successful (HTTP {response.status_code}) [{elapsed_ms:.0f}ms]")
                    # Only parse response occasionally to reduce overhead
                    if not PERFORMANCE_MODE or (hasattr(self, '_log_counter') and self._log_counter % 20 == 0):
                        try:
                            response_data = response.json()
                            self._debug_log_throttled(f"API Response: {response_data}")
                        except (json.JSONDecodeError, requests.exceptions.JSONDecodeError):
                            self._debug_log_throttled(f"API Response not valid JSON (Status: {response.status_code})")

                self.send_retries = 0 # Reset retries on success
                self.current_send_interval = DEFAULT_SEND_INTERVAL_S # Reset interval

                # Send to Data Cloud if enabled
                if self.datacloud_enabled and self.datacloud_client:
                    try:
                        self.datacloud_client.send_telemetry_record(payload)
                        if self.debug_mode:
                            self._debug_log_throttled("✅ Data Cloud telemetry sent successfully")
                    except Exception as e:
                        logging.error(f"❌ Failed to send telemetry to Data Cloud: {e}")

                # Reset aggregation ONLY after successful send of a completed lap payload
                if self.lap_just_completed:
                     logging.info(f"Resetting aggregation data for new lap ({self.current_lap_num}).")
                     self._reset_lap_aggregates()
                     self.lap_just_completed = False # Reset flag after processing

            else:
                # Log failure details
                logging.error(f"❌ Send failed (HTTP {response.status_code}) [{elapsed_ms:.0f}ms]")
                logging.error(f"   URL: {self.api_url}")
                logging.error(f"   Response: {response.text[:500]}") # Log beginning of response body
                self.connection_stats["total_failed"] += 1
                self.send_retries += 1 # Increment retries on failure

        # Specific exception handling
        except requests.exceptions.Timeout:
            elapsed_ms = (time.monotonic() - start_req_time) * 1000
            logging.error(f"⏱️ Send failed: Timeout after {elapsed_ms:.0f}ms")
            logging.error(f"   URL: {self.api_url}")
            self.connection_stats["total_failed"] += 1
            self.send_retries += 1
        except requests.exceptions.ConnectionError as e:
             elapsed_ms = (time.monotonic() - start_req_time) * 1000
             logging.error(f"❌ Send failed: Connection Error [{elapsed_ms:.0f}ms]")
             logging.error(f"   URL: {self.api_url}")
             logging.error(f"   Error: {e}")
             self.connection_stats["total_failed"] += 1
             self.send_retries += 1
        except requests.exceptions.RequestException as e:
             elapsed_ms = (time.monotonic() - start_req_time) * 1000
             logging.error(f"❌ Send failed: Request Exception [{elapsed_ms:.0f}ms]")
             logging.error(f"   URL: {self.api_url}")
             logging.error(f"   Error: {e}")
             self.connection_stats["total_failed"] += 1
             self.send_retries += 1
        # Catch-all for other unexpected errors during send
        except Exception as e:
             elapsed_ms = (time.monotonic() - start_req_time) * 1000
             logging.exception(f"💥 Unexpected error during send [{elapsed_ms:.0f}ms]")
             self.connection_stats["total_failed"] += 1
             self.send_retries += 1


    def _update_send_interval(self):
        """Adjusts send interval based on retry count using exponential backoff."""
        if self.send_retries == 0:
             # If interval was increased, gradually decrease it back to default?
             # For now, just reset directly to default.
             if self.current_send_interval != DEFAULT_SEND_INTERVAL_S:
                 logging.info(f"Send successful, resetting send interval to {DEFAULT_SEND_INTERVAL_S:.1f}s")
                 self.current_send_interval = DEFAULT_SEND_INTERVAL_S
        elif self.send_retries >= MAX_SEND_RETRIES: # Start backoff after MAX_SEND_RETRIES failures
            # Calculate exponential backoff
            backoff_multiplier = RETRY_BACKOFF_FACTOR ** (self.send_retries - MAX_SEND_RETRIES + 1)
            new_interval = min(DEFAULT_SEND_INTERVAL_S * backoff_multiplier, MAX_SEND_INTERVAL_S)
            # Only log if the interval actually changes
            if new_interval > self.current_send_interval:
                 self.current_send_interval = new_interval
                 logging.warning(f"Send failures detected. Increasing send interval to {self.current_send_interval:.1f}s (Retries: {self.send_retries})")

            # Optional: Reset retry count after a very long backoff period to prevent infinite increase
            if self.send_retries >= BACKOFF_RESET_THRESHOLD:
                 logging.warning(f"Resetting retry count from {self.send_retries} after prolonged backoff threshold reached.")
                 self.send_retries = 0 # Reset retries, interval will reset on next success
                 # Optionally reset interval immediately here too:
                 # self.current_send_interval = DEFAULT_SEND_INTERVAL_S

    def _print_status_update(self):
        """Logs a periodic status update with performance metrics."""
        now = time.time()
        elapsed_runtime = now - self.start_time
        packets_per_sec = self.packets_received / elapsed_runtime if elapsed_runtime > 0 else 0

        total_sent = self.connection_stats.get("total_sent", 0)
        total_failed = self.connection_stats.get("total_failed", 0)
        total_response_time = self.connection_stats.get("total_response_time", 0)

        avg_response_time_ms = (total_response_time / total_sent) if total_sent > 0 else 0
        success_rate = (100 * (total_sent - total_failed) / total_sent) if total_sent > 0 else 100

        # Get performance metrics
        try:
            process = psutil.Process()
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            memory_percent = process.memory_percent()
            num_threads = process.num_threads()
            
            # System metrics
            system_cpu = psutil.cpu_percent()
            system_memory = psutil.virtual_memory().percent
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            cpu_percent = memory_mb = memory_percent = num_threads = 0
            system_cpu = system_memory = 0

        # Always log status updates with INFO level for useful console output
        logging.info("============ TELEMETRY STATUS UPDATE ============")
        logging.info(f"  Driver: {self.driver_name} | Track: {self.track_name}")
        logging.info(f"  Uptime: {str(datetime.timedelta(seconds=int(elapsed_runtime)))}")
        logging.info(f"  Packets: {self.packets_received} ({packets_per_sec:.1f}/sec)")
        
        # Performance metrics
        logging.info(f"  Process: CPU {cpu_percent:.1f}% | Memory {memory_mb:.0f}MB ({memory_percent:.1f}%) | Threads {num_threads}")
        logging.info(f"  System:  CPU {system_cpu:.1f}% | Memory {system_memory:.1f}%")
        
        # Current race info (most important data)
        if self.latest_lap_data:
            lap_valid_str = "✓ Valid" if self.latest_lap_data.m_currentLapInvalid == 0 else "✗ Invalid"
            lap_time_sec = self.latest_lap_data.m_currentLapTimeInMS / 1000.0
            position = self.latest_lap_data.m_carPosition
            position_str = f"{position}{self._get_position_suffix(position)}"
            
            # Format nicely for readability
            logging.info(f"  Position: {position_str} | Lap: {self.current_lap_num} | Sector: {self.latest_lap_data.m_sector + 1}")
            logging.info(f"  Current Lap: {lap_time_sec:.3f}s ({lap_valid_str})")
            
            # Add last lap time if available
            if self.last_lap_time_ms > 0:
                last_lap_time = self.last_lap_time_ms / 1000.0
                logging.info(f"  Last Lap: {last_lap_time:.3f}s")
        else:
            logging.info("  Race Data: Waiting for telemetry...")
        
        # Car data
        if self.latest_telemetry:
            gear_display = str(self.latest_telemetry.m_gear)
            if self.latest_telemetry.m_gear == 0:
                gear_display = "N"
            elif self.latest_telemetry.m_gear == -1:
                gear_display = "R"
                
            throttle = int(self.latest_telemetry.m_throttle * 100)
            brake = int(self.latest_telemetry.m_brake * 100)
            drs = "ACTIVE" if self.latest_telemetry.m_drs == 1 else "inactive"
            
            logging.info(f"  Speed: {self.latest_telemetry.m_speed} km/h | Gear: {gear_display} | RPM: {self.latest_telemetry.m_engineRPM}")
            logging.info(f"  Throttle: {throttle}% | Brake: {brake}% | DRS: {drs}")
            
            # Show tyre temps if available
            if hasattr(self.latest_telemetry, 'm_tyresSurfaceTemperature') and len(self.latest_telemetry.m_tyresSurfaceTemperature) >= 4:
                logging.info(f"  Tyre Temps: FL:{self.latest_telemetry.m_tyresSurfaceTemperature[2]}°C FR:{self.latest_telemetry.m_tyresSurfaceTemperature[3]}°C")
                logging.info(f"              RL:{self.latest_telemetry.m_tyresSurfaceTemperature[0]}°C RR:{self.latest_telemetry.m_tyresSurfaceTemperature[1]}°C")
        
        # Car status
        if self.latest_car_status:
            tyre = TYRE_COMPOUND_MAP.get(self.latest_car_status.m_actualTyreCompound, "Unknown")
            fuel = self.latest_car_status.m_fuelInTank
            fuel_laps = self.latest_car_status.m_fuelRemainingLaps
            ers_mode = ERS_DEPLOY_MODE_MAP.get(self.latest_car_status.m_ersDeployMode, "Unknown")
            ers_pct = (self.latest_car_status.m_ersStoreEnergy / 4000000) * 100 if self.latest_car_status.m_ersStoreEnergy else 0
            
            logging.info(f"  Tyres: {tyre} | Fuel: {fuel:.1f}kg ({fuel_laps:.1f} laps)")
            logging.info(f"  ERS: {ers_pct:.0f}% | Mode: {ers_mode}")
            
        # Connection stats at the end
        logging.info(f"  Network: {total_sent} sends | {success_rate:.1f}% success | {avg_response_time_ms:.0f}ms latency")
        logging.info("================================================")
    
    def _debug_log_throttled(self, message: str, force: bool = False):
        """Log debug messages with throttling to reduce overhead"""
        if not PERFORMANCE_MODE or force:
            logging.debug(message)
            return
            
        current_time = time.time()
        
        # Only log if enough time has passed or if this is a critical message
        if (current_time - self._last_debug_log) >= LOG_THROTTLE_INTERVAL:
            logging.debug(f"[Throttled Logs] {message}")
            self._last_debug_log = current_time
            self._log_counter = 0
        else:
            self._log_counter += 1
            # Show a count every 100 throttled messages
            if self._log_counter % 100 == 0:
                logging.debug(f"[{self._log_counter} debug messages throttled]")

    def _get_position_suffix(self, position):
        """Returns the correct ordinal suffix for a position."""
        if position % 10 == 1 and position != 11:
            return "st"
        elif position % 10 == 2 and position != 12:
            return "nd"
        elif position % 10 == 3 and position != 13:
            return "rd"
        else:
            return "th"


    def run(self):
        """Starts the UDP listener and main processing loop."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((self.udp_ip, self.udp_port))
            self.sock.settimeout(SOCKET_TIMEOUT_S)
            logging.info(f"✅ Socket bound successfully to {self.udp_ip}:{self.udp_port}")
        except socket.error as e:
            logging.critical(f"🚨 Failed to bind socket: {e}. Check if port {self.udp_port} is already in use. Exiting.")
            return
        except Exception as e:
            logging.critical(f"🚨 Unexpected error during socket setup: {e}. Exiting.", exc_info=True)
            return

        logging.info("🚀 Starting main loop. Waiting for F1 telemetry data...")

        while True: # Main loop
            received_data = None # Ensure variable is defined for the scope
            addr = None
            try:
                # 1. Receive Data
                try:
                    received_data, addr = self.sock.recvfrom(PACKET_BUFFER_SIZE)
                    if self.packets_received == 0:
                        logging.info(f"✅ CONNECTED! Receiving F1 telemetry data from {addr}")
                    self.packets_received += 1
                except socket.timeout:
                    # Only log waiting message periodically if no packets ever received
                    if self.packets_received == 0 and time.time() - self.last_status_update_time > 15:
                         logging.info(f"⏳ Waiting for telemetry data from F1 game... (Make sure UDP is enabled in F1 game settings, port {self.udp_port})")
                         self.last_status_update_time = time.time() # Reset timer to avoid spamming
                    # Normal timeout when game is running is expected, just continue
                    pass # Continue loop to check for send interval etc.
                except socket.error as e:
                    logging.error(f"Socket error receiving data: {e}")
                    time.sleep(1) # Wait a bit before retrying
                    continue # Skip rest of the loop iteration

                # 2. Process Data (if received in this iteration)
                if received_data:
                    header = PacketHeader.from_bytes(received_data)
                    if not header:
                        logging.warning(f"Received data (from {addr}, {len(received_data)} bytes) too short for header or unpack failed.")
                        # Maybe log hex of small packet if debugging needed: logging.debug(f"Small packet hex: {received_data.hex()}")
                        received_data = None # Clear data
                        continue

                    # Check format (e.g., F1 24 is 2024) - CRITICAL CHECK
                    if header.m_packetFormat != 2024:
                         # Log only periodically or if it changes, to avoid spam if receiving old format
                         if self.packets_received % 100 == 1: # Log first time and then every 100 packets
                              logging.warning(f"Ignoring packet with format {header.m_packetFormat} (Expected 2024). Ensure game telemetry is set to F1 2024 format.")
                         received_data = None
                         continue

                    # Store player index if not yet set
                    if self.player_car_index == -1 and header.m_playerCarIndex != 255: # 255 means spectator
                        self.player_car_index = header.m_playerCarIndex
                        logging.info(f"Player car index identified: {self.player_car_index}")

                    # Only process packets if we know the player index (and it's valid)
                    if 0 <= self.player_car_index < self.NUM_CARS: # Check index validity
                        # Store the latest header for frame ID
                        self.latest_header = header
                        packet_data = received_data[PacketHeader.SIZE:]
                        packet_processed = False # Flag to check if any handler processed it

                        # --- Dispatch to Packet Handlers ---
                        if header.m_packetId == PACKET_ID_LAP_DATA:
                            # <<< ADDED DEBUGGING AROUND HERE >>>
                            logging.debug(f"Processing LAP_DATA packet (ID {header.m_packetId})")
                            logging.debug(f"Header Details: Format={header.m_packetFormat}, GameYear={header.m_gameYear}, PacketVer={header.m_packetVersion}, SessionTime={header.m_sessionTime:.3f}")
                            logging.debug(f"Size of packet_data payload for LapData: {len(packet_data)} bytes")
                            # <<< END DEBUGGING >>>
                            packet = PacketLapData.from_bytes(header, packet_data);
                            if packet:
                                self._handle_lap_data(packet)
                                packet_processed = True
                            else:
                                logging.warning(f"Failed to parse PacketLapData (Header: {header})")

                        elif header.m_packetId == PACKET_ID_CAR_TELEMETRY:
                            packet = PacketCarTelemetry.from_bytes(header, packet_data);
                            if packet:
                                self._handle_telemetry(packet)
                                packet_processed = True
                            else:
                                logging.warning(f"Failed to parse PacketCarTelemetry (Header: {header})")

                        elif header.m_packetId == PACKET_ID_CAR_STATUS:
                            packet = PacketCarStatus.from_bytes(header, packet_data);
                            if packet:
                                self._handle_car_status(packet)
                                packet_processed = True
                            else:
                                logging.warning(f"Failed to parse PacketCarStatus (Header: {header})")

                        elif header.m_packetId == PACKET_ID_CAR_DAMAGE:
                             packet = PacketCarDamage.from_bytes(header, packet_data) # Parse damage
                             if packet:
                                 self._handle_damage(packet)
                                 packet_processed = True # Handle damage
                             else:
                                logging.warning(f"Failed to parse PacketCarDamage (Header: {header})")

                        elif header.m_packetId == PACKET_ID_EVENT:
                            self._handle_event(header, packet_data)
                            packet_processed = True # Event handler doesn't return parsed packet

                        elif header.m_packetId == PACKET_ID_SESSION:
                            packet = PacketSessionData.from_bytes(header, packet_data)
                            if packet:
                                self._handle_session(packet)
                                packet_processed = True
                            else:
                                logging.warning(f"Failed to parse PacketSessionData (Header: {header})")

                        # --- End Packet Handlers ---

                        # Log if a packet ID was received but not handled by any 'if/elif' block above
                        # Filter out common noisy packets if they are not needed
                        ignored_packet_ids = {
                            PACKET_ID_MOTION, PACKET_ID_PARTICIPANTS,
                            PACKET_ID_CAR_SETUPS, PACKET_ID_FINAL_CLASSIFICATION, PACKET_ID_LOBBY_INFO,
                            PACKET_ID_SESSION_HISTORY, PACKET_ID_TYRE_SETS, PACKET_ID_MOTION_EX,
                            PACKET_ID_TIME_TRIAL
                        }
                        if not packet_processed and header.m_packetId not in ignored_packet_ids:
                              # Log less frequently to avoid spam
                              if self.packets_received % 50 == 1:
                                   logging.debug(f"Received unhandled packet ID: {header.m_packetId} (Header: {header})")
                    elif self.player_car_index == 255:
                        # Spectator mode, maybe log less frequently
                        if self.packets_received % 200 == 1:
                             logging.info("Receiving packets in spectator mode (PlayerIndex=255). Not processing player-specific data.")
                    else:
                        # Invalid player index, shouldn't happen if check above is correct
                        if self.packets_received % 100 == 1:
                            logging.warning(f"Invalid player car index ({self.player_car_index}). Cannot process player data.")


                    received_data = None # Clear data after processing attempt

                # 3. Send Periodically - Optimized for local operation
                now = time.time()
                if now - self.last_send_time >= self.current_send_interval:
                    # Skip send_interval adjustment for local operation to maximize throughput
                    # Always send a payload, even if no data is available yet
                    # This keeps the dashboard alive and responsive
                    self.executor.submit(self._send_payload, self.latest_header)
                    self.last_send_time = now # Update last send time *after* submitting

                # 4. Periodic Status Update (optimized interval)
                status_interval = STATUS_LOG_INTERVAL if PERFORMANCE_MODE else STATUS_UPDATE_INTERVAL_S
                if now - self.last_status_update_time >= status_interval:
                    self._print_status_update()
                    self.last_status_update_time = now

            except KeyboardInterrupt:
                logging.info("Keyboard interrupt received. Shutting down...")
                break # Exit the main loop
            except Exception as e:
                # Catch any unexpected errors in the main loop logic
                logging.exception("💥 Unexpected error in main loop.")
                time.sleep(5) # Pause briefly to prevent rapid error loops

        self.shutdown() # Clean up resources after loop exits


    def shutdown(self):
        """Cleans up resources like the socket and thread pool."""
        logging.info("🔌 Initiating shutdown sequence...")
        if self.sock:
            try:
                self.sock.close()
                logging.info("Socket closed.")
                self.sock = None
            except Exception as e:
                logging.error(f"Error closing socket: {e}")
        if self.executor:
            try:
                logging.info("Shutting down thread pool executor (waiting for tasks)...")
                # Allow tasks currently running to complete, don't wait indefinitely
                self.executor.shutdown(wait=True, cancel_futures=False)
                logging.info("Executor shutdown complete.")
                self.executor = None
            except Exception as e:
                logging.error(f"Error shutting down executor: {e}")
        logging.info(f"✅ {APP_NAME} shutdown complete.")


# --- Main Execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument('--debug', action='store_true', help='Enable detailed debug logging')
    parser.add_argument('--driver', type=str, default=DEFAULT_DRIVER_NAME, help='Driver name for API payload')
    parser.add_argument('--track', type=str, default=DEFAULT_TRACK_NAME, help='Track name for API payload (used as fallback if auto-detection fails)')
    parser.add_argument('--no-auto-track', action='store_true', help='Disable automatic track detection from game data')
    parser.add_argument('--url', type=str, required=True, help='Full URL of the telemetry API endpoint')
    parser.add_argument('--ip', type=str, default=DEFAULT_UDP_IP, help=f'IP address to bind UDP socket to (default: {DEFAULT_UDP_IP})')
    parser.add_argument('--port', type=int, default=DEFAULT_UDP_PORT, help=f'UDP port to listen on (default: {DEFAULT_UDP_PORT})')
    parser.add_argument('--server-port', type=int, default=8080, help='Port for the web server to send data to (default: 8080)')
    parser.add_argument('--datacloud', action='store_true', help='Enable Salesforce Data Cloud integration')
    args = parser.parse_args()

    # Basic validation and URL adjustment for server port
    if args.url.startswith(('http://', 'https://')):
        # If URL already valid, check if we need to adjust the port for localhost
        if "localhost" in args.url and args.server_port:
            args.url = args.url.replace(":5000/", f":{args.server_port}/")
            print(f"Adjusted URL to use port {args.server_port}: {args.url}")
    else:
        print(f"ERROR: Invalid URL provided: {args.url}. Please include http:// or https://", file=sys.stderr)
        sys.exit(1)

    bridge = None # Initialize bridge variable
    exit_code = 0
    try:
        bridge = TelemetryBridge(
            driver=args.driver,
            track=args.track,
            url=args.url,
            ip=args.ip,
            port=args.port,
            debug=args.debug,
            auto_detect_track=not args.no_auto_track,
            datacloud=args.datacloud
        )
        bridge.run() # Start the main loop
    except Exception as e:
        # Log critical errors that might occur during TelemetryBridge init or prevent run() call
        logging.critical(f"🚨 Unhandled critical error during bridge setup or execution: {e}", exc_info=True)
        exit_code = 1
    finally:
        # Ensure shutdown is called even if run() exits unexpectedly or KeyboardInterrupt occurs
        if bridge and bridge.executor is not None: # Check if bridge and executor exist
             logging.info("Ensuring final shutdown in finally block...")
             bridge.shutdown()
    sys.exit(exit_code)