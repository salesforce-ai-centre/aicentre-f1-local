#!/usr/bin/env python3
"""
Analyze recorded F1 UDP packets to understand the data
Usage:
    python3 scripts/analyze_udp_packets.py --input recordings/rig_a.packets
"""

import argparse
import struct
import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from receiver import PacketHeader, PacketLapData

def analyze_packets(input_file, show_details=False):
    """
    Analyze recorded UDP packets and show statistics

    Args:
        input_file: File containing recorded packets
        show_details: Show detailed packet information
    """
    print(f"🔍 Analyzing UDP packets from: {input_file}\n")

    # Read metadata
    with open(input_file, 'rb') as f:
        metadata_size = struct.unpack('<I', f.read(4))[0]
        metadata_json = f.read(metadata_size)
        metadata = json.loads(metadata_json.decode('utf-8'))

        print(f"📊 Recording Metadata:")
        print(f"   Recorded: {metadata.get('recording_start', 'unknown')}")
        print(f"   Port: {metadata.get('port', 'unknown')}")
        print(f"   Total packets: {metadata.get('packet_count', 'unknown')}")
        print(f"   Duration: {metadata.get('duration', 'unknown')}s")
        print()

        # Skip separator
        separator = f.readline()

        # Packet statistics
        packet_types = {}
        player_indices = set()
        session_uids = set()
        total_packets = 0

        # Track specific packet data
        lap_data_samples = []
        positions_seen = set()
        lap_times_seen = []

        print("📦 Parsing packets...\n")

        while True:
            timestamp_bytes = f.read(8)
            if not timestamp_bytes:
                break

            timestamp = struct.unpack('<d', timestamp_bytes)[0]
            packet_size = struct.unpack('<I', f.read(4))[0]
            packet_data = f.read(packet_size)

            total_packets += 1

            # Parse packet header
            if len(packet_data) >= PacketHeader.SIZE:
                try:
                    header = PacketHeader.from_bytes(packet_data)
                    if header:
                        packet_id = header.m_packetId
                        packet_types[packet_id] = packet_types.get(packet_id, 0) + 1
                        player_indices.add(header.m_playerCarIndex)
                        session_uids.add(header.m_sessionUID)

                        # Parse lap data packets for detailed info
                        if packet_id == 2 and show_details:  # Lap Data packet
                            try:
                                lap_packet = PacketLapData.from_bytes(header, packet_data[PacketHeader.SIZE:])
                                if lap_packet and lap_packet.m_lapData:
                                    player_lap = lap_packet.m_lapData[header.m_playerCarIndex]
                                    lap_data_samples.append({
                                        'timestamp': timestamp,
                                        'player_index': header.m_playerCarIndex,
                                        'position': player_lap.m_carPosition,
                                        'lap_num': player_lap.m_currentLapNum,
                                        'current_lap_time_ms': player_lap.m_currentLapTimeInMS,
                                        'last_lap_time_ms': player_lap.m_lastLapTimeInMS,
                                        'lap_distance': player_lap.m_lapDistance,
                                        'result_status': player_lap.m_resultStatus,
                                        'driver_status': player_lap.m_driverStatus
                                    })
                                    positions_seen.add(player_lap.m_carPosition)
                                    if player_lap.m_lastLapTimeInMS > 0:
                                        lap_times_seen.append(player_lap.m_lastLapTimeInMS)
                            except Exception as e:
                                pass

                except Exception as e:
                    pass

    # Print analysis
    print(f"📈 Packet Statistics:")
    print(f"   Total packets parsed: {total_packets}")
    print(f"   Unique session UIDs: {len(session_uids)}")
    print(f"   Player indices seen: {sorted(player_indices)}")
    print()

    # Packet type breakdown
    packet_names = {
        0: "Motion", 1: "Session", 2: "Lap Data", 3: "Event",
        4: "Participants", 5: "Car Setups", 6: "Car Telemetry",
        7: "Car Status", 8: "Final Classification", 9: "Lobby Info",
        10: "Car Damage", 11: "Session History", 12: "Tyre Sets",
        13: "Motion Ex", 14: "Time Trial", 15: "Lap Positions"
    }

    print(f"📊 Packet Type Breakdown:")
    for packet_id in sorted(packet_types.keys()):
        name = packet_names.get(packet_id, f"Unknown ({packet_id})")
        count = packet_types[packet_id]
        percentage = (count / total_packets * 100) if total_packets > 0 else 0
        print(f"   {packet_id:2d} - {name:20s}: {count:6d} packets ({percentage:5.1f}%)")

    if lap_data_samples:
        print(f"\n🏁 Lap Data Analysis:")
        print(f"   Lap data packets: {len(lap_data_samples)}")
        print(f"   Positions seen: {sorted(positions_seen)}")
        if lap_times_seen:
            avg_lap = sum(lap_times_seen) / len(lap_times_seen)
            print(f"   Lap times recorded: {len(lap_times_seen)}")
            print(f"   Average lap time: {avg_lap/1000:.3f}s")
            print(f"   Best lap time: {min(lap_times_seen)/1000:.3f}s")

        if show_details and len(lap_data_samples) > 0:
            print(f"\n📋 Sample Lap Data (first 5 packets):")
            for i, sample in enumerate(lap_data_samples[:5]):
                print(f"\n   Packet {i+1}:")
                print(f"      Timestamp: {sample['timestamp']:.3f}")
                print(f"      Player Index: {sample['player_index']}")
                print(f"      Position: {sample['position']}")
                print(f"      Lap: {sample['lap_num']}")
                print(f"      Current Lap Time: {sample['current_lap_time_ms']}ms")
                print(f"      Last Lap Time: {sample['last_lap_time_ms']}ms")
                print(f"      Lap Distance: {sample['lap_distance']:.1f}m")
                print(f"      Result Status: {sample['result_status']}")
                print(f"      Driver Status: {sample['driver_status']}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze recorded F1 UDP telemetry packets')
    parser.add_argument('--input', type=str, required=True, help='Input file path (e.g., recordings/rig_a.packets)')
    parser.add_argument('--details', action='store_true', help='Show detailed packet information')

    args = parser.parse_args()

    analyze_packets(
        input_file=args.input,
        show_details=args.details
    )
