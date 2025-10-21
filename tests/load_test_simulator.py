#!/usr/bin/env python3
"""
F1 Dashboard Load Testing Simulator
Simulates high-frequency F1 telemetry data to test dashboard performance under load
"""

import socket
import struct
import time
import threading
import argparse
import logging
import random
import sys
from typing import List, Dict, Any
from dataclasses import dataclass

# Packet structure constants (from F1 24 spec)
PACKET_FORMAT = 2024
GAME_YEAR = 24
PACKET_VERSION = 1

@dataclass
class TestConfig:
    packets_per_second: float = 60.0  # Normal F1 game frequency
    duration_seconds: int = 300  # 5 minutes default
    num_cars: int = 22
    target_host: str = "127.0.0.1"
    target_port: int = 20777
    stress_test: bool = False
    verbose: bool = False

class F1PacketSimulator:
    """Simulates F1 24 UDP telemetry packets for load testing"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.socket = None
        self.running = False
        self.packets_sent = 0
        self.start_time = 0
        
        # Simulation state
        self.session_time = 0.0
        self.frame_id = 0
        self.lap_number = 1
        self.lap_time_ms = 0
        self.sector = 0
        self.position = 1
        
        # Car state for realistic data
        self.speed = 0
        self.rpm = 1000
        self.gear = 1
        self.throttle = 0.0
        self.brake = 0.0
        self.steering = 0.0
        self.lap_distance = 0.0
        
        self.setup_logging()
    
    def setup_logging(self):
        level = logging.DEBUG if self.config.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s [%(levelname)s] %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def create_packet_header(self, packet_id: int) -> bytes:
        """Create F1 24 packet header"""
        header_format = "<HBBBBBQfIIBB"
        
        header_data = (
            PACKET_FORMAT,      # m_packetFormat
            GAME_YEAR,          # m_gameYear
            1,                  # m_gameMajorVersion
            0,                  # m_gameMinorVersion
            PACKET_VERSION,     # m_packetVersion
            packet_id,          # m_packetId
            12345678,           # m_sessionUID
            self.session_time,  # m_sessionTime
            self.frame_id,      # m_frameIdentifier
            self.frame_id + 100000,  # m_overallFrameIdentifier
            0,                  # m_playerCarIndex
            255                 # m_secondaryPlayerCarIndex
        )
        
        return struct.pack(header_format, *header_data)
    
    def create_lap_data_packet(self) -> bytes:
        """Create a lap data packet"""
        header = self.create_packet_header(2)  # PACKET_ID_LAP_DATA = 2
        
        # Lap data format for one car (simplified)
        lap_data_format = "<" + "II HBHB HBHB fff BBBB BBB Bf BBB" * self.config.num_cars
        
        lap_data_values = []
        for car_idx in range(self.config.num_cars):
            # Vary data slightly for each car
            car_lap_time = self.lap_time_ms + random.randint(-1000, 1000)
            car_position = min(car_idx + 1, 22)
            car_lap_distance = self.lap_distance + random.uniform(-100, 100)
            
            lap_data_values.extend([
                max(0, self.lap_time_ms - 90000),  # m_lastLapTimeInMS
                car_lap_time,                      # m_currentLapTimeInMS
                random.randint(20000, 30000),      # m_sector1TimeMSPart
                0,                                 # m_sector1TimeMinutesPart
                random.randint(25000, 35000),      # m_sector2TimeMSPart
                0,                                 # m_sector2TimeMinutesPart
                random.randint(-1000, 1000),       # m_deltaToCarInFrontMSPart
                0,                                 # m_deltaToCarInFrontMinutesPart
                random.randint(-5000, 5000),       # m_deltaToRaceLeaderMSPart
                0,                                 # m_deltaToRaceLeaderMinutesPart
                max(0, car_lap_distance),          # m_lapDistance
                car_lap_distance + (self.lap_number - 1) * 5000,  # m_totalDistance
                random.uniform(-2.0, 2.0),         # m_safetyCarDelta
                car_position,                      # m_carPosition
                0,                                 # m_currentLapNum (will be set correctly)
                0,                                 # m_pitStatus
                random.randint(0, 3),              # m_numPitStops
                self.sector,                       # m_sector
                0,                                 # m_currentLapInvalid
                0,                                 # m_penalties
                0,                                 # m_totalWarnings
                0,                                 # m_cornerCuttingWarnings
                random.randint(1, 20),             # m_numUnservedDriveThroughPens
                random.randint(1, 20),             # m_numUnservedStopGoPens
                random.randint(0, 3),              # m_gridPosition
                0,                                 # m_driverStatus
                0,                                 # m_resultStatus
                0,                                 # m_pitLaneTimerActive
                random.randint(15000, 20000),      # m_pitLaneTimeInLaneInMS
                random.randint(2000, 4000),        # m_pitStopTimerInMS
                0                                  # m_pitStopShouldServePen
            ])
        
        # Set correct lap number for player car (car 0)
        if len(lap_data_values) >= 15:
            lap_data_values[14] = self.lap_number
        
        try:
            data = struct.pack(lap_data_format, *lap_data_values)
            return header + data
        except struct.error as e:
            self.logger.error(f"Error packing lap data: {e}")
            return header  # Return just header if packing fails
    
    def create_telemetry_packet(self) -> bytes:
        """Create a car telemetry packet"""
        header = self.create_packet_header(6)  # PACKET_ID_CAR_TELEMETRY = 6
        
        # Simplified telemetry data for all cars
        telemetry_data = []
        
        for car_idx in range(self.config.num_cars):
            # Add some variation between cars
            car_speed = max(0, self.speed + random.uniform(-20, 20))
            car_rpm = max(1000, self.rpm + random.randint(-500, 500))
            car_gear = max(-1, min(8, self.gear + random.randint(-1, 1)))
            
            # Brake temperatures (4 values)
            brake_temps = [random.randint(200, 800) for _ in range(4)]
            
            # Tyre surface temperatures (4 values)
            tyre_surface_temps = [random.randint(80, 120) for _ in range(4)]
            
            # Tyre inner temperatures (4 values)
            tyre_inner_temps = [random.randint(85, 125) for _ in range(4)]
            
            # Tyre pressures (4 values)
            tyre_pressures = [random.uniform(18.0, 25.0) for _ in range(4)]
            
            # Surface types (4 values)
            surface_types = [random.randint(0, 16) for _ in range(4)]
            
            telemetry_entry = [
                int(car_speed),                    # m_speed
                self.throttle,                     # m_throttle
                self.steering,                     # m_steer
                self.brake,                        # m_brake
                random.uniform(0, 1),              # m_clutch
                car_gear,                          # m_gear
                car_rpm,                           # m_engineRPM
                random.randint(0, 1),              # m_drs
                random.randint(0, 100),            # m_revLightsPercent
                random.randint(0, 32767),          # m_revLightsBitValue
            ]
            
            # Add arrays
            telemetry_entry.extend(brake_temps)
            telemetry_entry.extend(tyre_surface_temps)
            telemetry_entry.extend(tyre_inner_temps)
            telemetry_entry.append(random.randint(80, 110))  # m_engineTemperature
            telemetry_entry.extend(tyre_pressures)
            telemetry_entry.extend(surface_types)
            
            telemetry_data.extend(telemetry_entry)
        
        # Add packet-level fields
        telemetry_data.extend([
            0,   # m_mfdPanelIndex
            255, # m_mfdPanelIndexSecondaryPlayer
            self.gear  # m_suggestedGear
        ])
        
        # Create format string
        single_car_format = "<H fff B H BBBB HHHH HHHHf ffff BBBB"
        telemetry_format = single_car_format[1:] * self.config.num_cars + "BBb"
        
        try:
            data = struct.pack("<" + telemetry_format[1:], *telemetry_data)
            return header + data
        except (struct.error, ValueError) as e:
            self.logger.error(f"Error packing telemetry data: {e}")
            return header
    
    def update_simulation_state(self):
        """Update simulation state for realistic progression"""
        # Simulate car movement and racing
        if self.frame_id % 20 == 0:  # Update every ~0.33 seconds
            # Simulate acceleration/deceleration
            if random.random() < 0.1:  # 10% chance to change inputs
                self.throttle = random.uniform(0, 1)
                self.brake = random.uniform(0, 0.8) if self.throttle < 0.3 else 0
                self.steering = random.uniform(-0.5, 0.5)
            
            # Update speed based on inputs
            if self.throttle > self.brake:
                self.speed = min(350, self.speed + (self.throttle * 5))
                self.rpm = min(13000, self.rpm + 100)
            else:
                self.speed = max(0, self.speed - (self.brake * 10))
                self.rpm = max(1000, self.rpm - 200)
            
            # Update gear based on RPM
            if self.rpm > 8000 and self.gear < 8:
                self.gear += 1
                self.rpm -= 2000
            elif self.rpm < 3000 and self.gear > 1:
                self.gear -= 1
                self.rpm += 1500
        
        # Update lap progression
        distance_increment = max(1, self.speed * 0.016667)  # Approximate distance per frame
        self.lap_distance += distance_increment
        
        # Lap progression (approximate 5km lap)
        if self.lap_distance > 5000:
            self.lap_number += 1
            self.lap_distance = 0
            self.lap_time_ms = 0
            self.sector = 0
            self.logger.info(f"Simulated lap {self.lap_number - 1} completed")
        
        # Sector progression
        if self.lap_distance > 1666 and self.sector == 0:
            self.sector = 1
        elif self.lap_distance > 3333 and self.sector == 1:
            self.sector = 2
        
        # Update lap time
        self.lap_time_ms += 16  # ~16ms per frame at 60fps
        
        # Update session time and frame ID
        self.session_time += 0.016667  # ~60fps
        self.frame_id += 1
    
    def send_packet(self, packet_data: bytes):
        """Send a packet via UDP"""
        try:
            self.socket.sendto(packet_data, (self.config.target_host, self.config.target_port))
            self.packets_sent += 1
        except Exception as e:
            self.logger.error(f"Error sending packet: {e}")
    
    def run_simulation(self):
        """Run the main simulation loop"""
        self.logger.info(f"Starting F1 load test simulation...")
        self.logger.info(f"Target: {self.config.target_host}:{self.config.target_port}")
        self.logger.info(f"Frequency: {self.config.packets_per_second} packets/sec")
        self.logger.info(f"Duration: {self.config.duration_seconds} seconds")
        self.logger.info(f"Stress test: {'Yes' if self.config.stress_test else 'No'}")
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.running = True
            self.start_time = time.time()
            
            packet_interval = 1.0 / self.config.packets_per_second
            next_packet_time = time.time()
            
            while self.running and (time.time() - self.start_time) < self.config.duration_seconds:
                current_time = time.time()
                
                if current_time >= next_packet_time:
                    # Update simulation state
                    self.update_simulation_state()
                    
                    # Send different packet types
                    if self.frame_id % 3 == 0:  # Send lap data every 3rd frame
                        packet = self.create_lap_data_packet()
                        self.send_packet(packet)
                    
                    if self.frame_id % 2 == 0:  # Send telemetry every 2nd frame
                        packet = self.create_telemetry_packet()
                        self.send_packet(packet)
                    
                    # In stress test mode, send additional packets
                    if self.config.stress_test:
                        for _ in range(3):  # Send 3x more packets
                            packet = self.create_telemetry_packet()
                            self.send_packet(packet)
                    
                    next_packet_time += packet_interval
                    
                    # Log progress
                    if self.packets_sent % 1000 == 0:
                        elapsed = time.time() - self.start_time
                        rate = self.packets_sent / elapsed
                        self.logger.info(f"Sent {self.packets_sent} packets in {elapsed:.1f}s ({rate:.1f} pps)")
                
                # Small sleep to prevent CPU spinning
                time.sleep(0.001)
                
        except KeyboardInterrupt:
            self.logger.info("Simulation interrupted by user")
        except Exception as e:
            self.logger.error(f"Simulation error: {e}")
        finally:
            self.running = False
            if self.socket:
                self.socket.close()
            
            # Final statistics
            elapsed = time.time() - self.start_time
            avg_rate = self.packets_sent / elapsed if elapsed > 0 else 0
            self.logger.info(f"Simulation completed:")
            self.logger.info(f"  Total packets sent: {self.packets_sent}")
            self.logger.info(f"  Duration: {elapsed:.1f} seconds")
            self.logger.info(f"  Average rate: {avg_rate:.1f} packets/sec")
            self.logger.info(f"  Final lap: {self.lap_number}")

def main():
    parser = argparse.ArgumentParser(description='F1 Dashboard Load Test Simulator')
    parser.add_argument('--host', default='127.0.0.1', help='Target host (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=20777, help='Target port (default: 20777)')
    parser.add_argument('--pps', type=float, default=60.0, help='Packets per second (default: 60)')
    parser.add_argument('--duration', type=int, default=300, help='Test duration in seconds (default: 300)')
    parser.add_argument('--cars', type=int, default=22, help='Number of cars to simulate (default: 22)')
    parser.add_argument('--stress', action='store_true', help='Enable stress test mode (3x packet rate)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    config = TestConfig(
        packets_per_second=args.pps,
        duration_seconds=args.duration,
        num_cars=args.cars,
        target_host=args.host,
        target_port=args.port,
        stress_test=args.stress,
        verbose=args.verbose
    )
    
    simulator = F1PacketSimulator(config)
    simulator.run_simulation()

if __name__ == "__main__":
    main()