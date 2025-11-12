#!/usr/bin/env python3
"""
Playback recorded F1 UDP packets for debugging
Usage:
    python3 scripts/playback_udp_packets.py --input recordings/rig_a.packets --port 20777 --speed 1.0
"""

import socket
import time
import argparse
import struct
import json

def playback_udp_packets(input_file, target_host, target_port, speed=1.0, loop=False):
    """
    Playback recorded UDP packets

    Args:
        input_file: File containing recorded packets
        target_host: Host to send packets to (e.g., 'localhost')
        target_port: Port to send packets to
        speed: Playback speed multiplier (1.0 = real-time, 2.0 = 2x speed, 0.5 = half speed)
        loop: Loop playback indefinitely
    """
    # Create UDP socket for sending
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Increase send buffer size to handle larger F1 packets (up to 64KB)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
    except OSError as e:
        print(f"⚠️  Warning: Could not set socket buffer size: {e}")

    print(f"📼 Playing back UDP packets")
    print(f"📁 Input file: {input_file}")
    print(f"🎯 Target: {target_host}:{target_port}")
    print(f"⏩ Speed: {speed}x")
    print(f"🔁 Loop: {'Yes' if loop else 'No'}")

    # Read metadata
    with open(input_file, 'rb') as f:
        metadata_size = struct.unpack('<I', f.read(4))[0]
        metadata_json = f.read(metadata_size)
        metadata = json.loads(metadata_json.decode('utf-8'))

        print(f"\n📊 Recording Info:")
        print(f"   Recorded: {metadata.get('recording_start', 'unknown')}")
        print(f"   Packets: {metadata.get('packet_count', 'unknown')}")
        print(f"   Duration: {metadata.get('duration', 'unknown')}s")
        print(f"\nPress Ctrl+C to stop playback\n")

        # Skip separator
        separator = f.readline()

        # Read all packets into memory
        packets = []
        while True:
            timestamp_bytes = f.read(8)
            if not timestamp_bytes:
                break

            timestamp = struct.unpack('<d', timestamp_bytes)[0]
            packet_size = struct.unpack('<I', f.read(4))[0]
            packet_data = f.read(packet_size)

            packets.append((timestamp, packet_data))

    print(f"✅ Loaded {len(packets)} packets from file\n")

    try:
        playback_count = 0
        while True:
            print(f"▶️  Starting playback (iteration {playback_count + 1})")

            start_time = time.time()
            first_packet_timestamp = packets[0][0] if packets else 0

            for i, (original_timestamp, packet_data) in enumerate(packets):
                # Calculate when this packet should be sent relative to playback start
                relative_time = (original_timestamp - first_packet_timestamp) / speed
                target_time = start_time + relative_time

                # Wait until it's time to send this packet
                sleep_time = target_time - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)

                # Send packet
                sock.sendto(packet_data, (target_host, target_port))

                # Progress update every 60 packets
                if (i + 1) % 60 == 0:
                    elapsed = time.time() - start_time
                    progress = (i + 1) / len(packets) * 100
                    print(f"📡 Sent {i + 1}/{len(packets)} packets ({progress:.1f}%) - {elapsed:.1f}s elapsed")

            playback_count += 1
            elapsed = time.time() - start_time

            print(f"✅ Playback complete ({len(packets)} packets in {elapsed:.1f}s)")

            if not loop:
                break

            print(f"🔁 Looping... (press Ctrl+C to stop)\n")

    except KeyboardInterrupt:
        print(f"\n⏹️  Playback stopped by user")

    finally:
        sock.close()
        print(f"\n📊 Total playback iterations: {playback_count}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Playback recorded F1 UDP telemetry packets')
    parser.add_argument('--input', type=str, required=True, help='Input file path (e.g., recordings/rig_a.packets)')
    parser.add_argument('--host', type=str, default='localhost', help='Target host (default: localhost)')
    parser.add_argument('--port', type=int, default=20777, help='Target UDP port (default: 20777)')
    parser.add_argument('--speed', type=float, default=1.0, help='Playback speed multiplier (default: 1.0)')
    parser.add_argument('--loop', action='store_true', help='Loop playback indefinitely')

    args = parser.parse_args()

    playback_udp_packets(
        input_file=args.input,
        target_host=args.host,
        target_port=args.port,
        speed=args.speed,
        loop=args.loop
    )
