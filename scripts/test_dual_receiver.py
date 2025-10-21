#!/usr/bin/env python3
"""
Test script for dual-rig UDP reception
Verifies that both sim PCs can send telemetry to this host
"""

import sys
import os
import time
import signal
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from telemetry_gateway import TelemetryGateway, RigConfig
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TelemetryMonitor:
    """Simple monitor to display received telemetry"""

    def __init__(self):
        self.rig_data = {}
        self.last_display = time.time()
        self.display_interval = 1.0  # Display every second

    def on_packet(self, rig_id: str, packet_data: dict):
        """Callback when packet is received"""
        # Update rig data
        self.rig_data[rig_id] = packet_data

        # Display at regular intervals
        if time.time() - self.last_display >= self.display_interval:
            self.display_status()
            self.last_display = time.time()

    def display_status(self):
        """Display current telemetry status"""
        os.system('clear' if os.name == 'posix' else 'cls')

        print("=" * 80)
        print("F1 25 DUAL-RIG TELEMETRY MONITOR")
        print("=" * 80)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        if not self.rig_data:
            print("⏳ Waiting for telemetry data...")
            print()
            print("Make sure both sim PCs have F1 25 configured:")
            print("  - UDP Telemetry: ON")
            print("  - UDP Format: 2025")
            print("  - IP Address: <this PC's IP>")
            print("  - RIG A → Port 20777")
            print("  - RIG B → Port 20778")
            return

        for rig_id in sorted(self.rig_data.keys()):
            data = self.rig_data[rig_id]
            self._display_rig(rig_id, data)

    def _display_rig(self, rig_id: str, data: dict):
        """Display telemetry for a single rig"""
        print(f"{'🔴' if rig_id == 'RIG_A' else '🔵'} {rig_id} - {data.get('driver_name', 'Unknown')}")
        print("-" * 40)

        # Session info
        session_uid = data.get('sessionUID', 'N/A')
        frame = data.get('overallFrameIdentifier', 0)
        print(f"  Session: {session_uid} | Frame: {frame}")

        # Packet-specific data
        packet_id = data.get('packetId')

        if packet_id == 6:  # Telemetry
            speed = data.get('speed', 0)
            rpm = data.get('engineRPM', 0)
            gear = data.get('gear', 0)
            throttle = data.get('throttle', 0) * 100
            brake = data.get('brake', 0) * 100

            print(f"  Speed: {speed} km/h | RPM: {rpm}")
            print(f"  Gear: {gear} | Throttle: {throttle:.0f}% | Brake: {brake:.0f}%")

            # Tyre temps (RL, RR, FL, FR)
            temps = data.get('tyresSurfaceTemperature', [0, 0, 0, 0])
            print(f"  Tyres: FL:{temps[2]}°C FR:{temps[3]}°C RL:{temps[0]}°C RR:{temps[1]}°C")

        elif packet_id == 2:  # Lap Data
            lap = data.get('currentLapNum', 0)
            position = data.get('carPosition', 0)
            lap_time = data.get('currentLapTimeInMS', 0) / 1000
            print(f"  Lap: {lap} | Position: {position} | Time: {lap_time:.3f}s")

        elif packet_id == 7:  # Car Status
            fuel = data.get('fuelInTank', 0)
            fuel_laps = data.get('fuelRemainingLaps', 0)
            drs = "ON" if data.get('drsAllowed') else "OFF"
            print(f"  Fuel: {fuel:.1f}kg ({fuel_laps:.1f} laps) | DRS: {drs}")

        elif packet_id == 10:  # Damage
            fl_wing = data.get('frontLeftWingDamage', 0)
            fr_wing = data.get('frontRightWingDamage', 0)
            engine = data.get('engineDamage', 0)
            print(f"  Damage: FL:{fl_wing}% FR:{fr_wing}% Engine:{engine}%")

        print()


def main():
    """Main entry point"""
    logger.info("Starting dual-rig telemetry test")

    # Configure rigs
    rigs = [
        RigConfig(
            rig_id="RIG_A",
            udp_port=20777,
            driver_name=os.environ.get("DRIVER_A_NAME", "Driver A"),
            device_id="SIM_A"
        ),
        RigConfig(
            rig_id="RIG_B",
            udp_port=20778,
            driver_name=os.environ.get("DRIVER_B_NAME", "Driver B"),
            device_id="SIM_B"
        )
    ]

    # Create monitor
    monitor = TelemetryMonitor()

    # Create gateway
    gateway = TelemetryGateway(
        rigs=rigs,
        event_callback=monitor.on_packet
    )

    # Handle shutdown gracefully
    def signal_handler(sig, frame):
        logger.info("\nShutting down...")
        gateway.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start gateway
    try:
        gateway.start()

        # Display network info
        print("\n" + "=" * 80)
        print("DUAL-RIG TELEMETRY RECEIVER STARTED")
        print("=" * 80)
        print("\nListening on:")
        print(f"  🔴 RIG A: UDP port 20777 (Driver: {rigs[0].driver_name})")
        print(f"  🔵 RIG B: UDP port 20778 (Driver: {rigs[1].driver_name})")
        print("\nConfigure your F1 25 game on each sim PC to send UDP to:")
        print(f"  IP Address: <this PC's IP address>")
        print(f"  UDP Format: 2025")
        print(f"  Send Rate: 60 Hz")
        print("\nPress Ctrl+C to stop")
        print("=" * 80)
        print()

        # Keep running
        while True:
            time.sleep(1)

            # Periodically log status
            if int(time.time()) % 10 == 0:
                status = gateway.get_status()
                logger.info(f"Gateway status: {status['rigs']}")

    except KeyboardInterrupt:
        logger.info("\nReceived interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        gateway.stop()


if __name__ == '__main__':
    main()
