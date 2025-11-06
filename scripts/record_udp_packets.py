#!/usr/bin/env python3
"""
Record F1 UDP packets to file for debugging and playback
Usage:
    python3 scripts/record_udp_packets.py --port 20777 --output recordings/rig_a.packets --duration 60
"""

import socket
import time
import argparse
import struct
import json
import os
from datetime import datetime

def record_udp_packets(port, output_file, duration=60, max_packets=None):
    """
    Record UDP packets from F1 game to file

    Args:
        port: UDP port to listen on
        output_file: File to write packets to
        duration: Maximum recording duration in seconds (None = unlimited)
        max_packets: Maximum number of packets to record (None = unlimited)
    """
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)

    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', port))
    sock.settimeout(1.0)

    print(f"🎙️  Recording UDP packets on port {port}")
    print(f"📝 Output file: {output_file}")
    print(f"⏱️  Duration: {duration}s" if duration else "⏱️  Duration: unlimited")
    print(f"📦 Max packets: {max_packets}" if max_packets else "📦 Max packets: unlimited")
    print(f"\nPress Ctrl+C to stop recording\n")

    start_time = time.time()
    packet_count = 0

    # Metadata
    metadata = {
        'recording_start': datetime.utcnow().isoformat(),
        'port': port,
        'packet_count': 0,
        'duration': 0
    }

    try:
        with open(output_file, 'wb') as f:
            # Write placeholder metadata header (will update at end)
            metadata_json = json.dumps(metadata).encode('utf-8')
            metadata_size = len(metadata_json)
            f.write(struct.pack('<I', metadata_size))  # Metadata size (4 bytes)
            f.write(metadata_json)
            f.write(b'\n---PACKETS---\n')  # Separator

            while True:
                # Check duration limit
                if duration and (time.time() - start_time) >= duration:
                    print(f"\n⏰ Duration limit reached ({duration}s)")
                    break

                # Check packet count limit
                if max_packets and packet_count >= max_packets:
                    print(f"\n📦 Packet limit reached ({max_packets} packets)")
                    break

                try:
                    data, addr = sock.recvfrom(2048)
                    timestamp = time.time()

                    # Write packet to file: [timestamp (8 bytes), size (4 bytes), data]
                    f.write(struct.pack('<d', timestamp))  # Timestamp (double)
                    f.write(struct.pack('<I', len(data)))  # Packet size (uint32)
                    f.write(data)  # Raw packet data

                    packet_count += 1

                    # Progress update every 60 packets (~1 second at 60Hz)
                    if packet_count % 60 == 0:
                        elapsed = time.time() - start_time
                        print(f"📊 Recorded {packet_count} packets in {elapsed:.1f}s ({packet_count/elapsed:.1f} pkt/s)")

                except socket.timeout:
                    # Check if we should continue waiting
                    if packet_count == 0:
                        print(".", end='', flush=True)
                    continue

    except KeyboardInterrupt:
        print(f"\n\n⏹️  Recording stopped by user")

    finally:
        # Update metadata
        elapsed = time.time() - start_time
        metadata['packet_count'] = packet_count
        metadata['duration'] = elapsed
        metadata['recording_end'] = datetime.utcnow().isoformat()

        # Rewrite metadata at start of file
        with open(output_file, 'r+b') as f:
            metadata_json = json.dumps(metadata, indent=2).encode('utf-8')
            new_metadata_size = len(metadata_json)
            f.seek(0)
            f.write(struct.pack('<I', new_metadata_size))
            f.write(metadata_json)

        sock.close()

        print(f"\n✅ Recording complete!")
        print(f"   Packets recorded: {packet_count}")
        print(f"   Duration: {elapsed:.1f}s")
        print(f"   Average rate: {packet_count/elapsed:.1f} packets/second")
        print(f"   File size: {os.path.getsize(output_file) / 1024:.1f} KB")
        print(f"   Output file: {output_file}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Record F1 UDP telemetry packets')
    parser.add_argument('--port', type=int, default=20777, help='UDP port to listen on (default: 20777)')
    parser.add_argument('--output', type=str, required=True, help='Output file path (e.g., recordings/rig_a.packets)')
    parser.add_argument('--duration', type=int, default=60, help='Recording duration in seconds (default: 60, 0=unlimited)')
    parser.add_argument('--max-packets', type=int, default=None, help='Maximum number of packets to record')

    args = parser.parse_args()

    duration = None if args.duration == 0 else args.duration

    record_udp_packets(
        port=args.port,
        output_file=args.output,
        duration=duration,
        max_packets=args.max_packets
    )
