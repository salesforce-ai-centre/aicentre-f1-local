#!/usr/bin/env python3
"""
Record UDP packets from multiple rigs simultaneously.
This is useful when running spectator view on the receiver PC.
"""

import socket
import struct
import json
import sys
import time
import signal
import threading
from datetime import datetime
from pathlib import Path

class MultiRigRecorder:
    def __init__(self, output_dir, ports):
        """
        Initialize multi-rig recorder.

        Args:
            output_dir: Directory to save recording files
            ports: List of port numbers to record from
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.ports = ports
        self.sockets = {}
        self.files = {}
        self.threads = {}
        self.running = True
        self.packet_counts = {port: 0 for port in ports}
        self.start_time = time.time()

        # Set up signal handler for clean shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        print("\n\n🛑 Stopping recording...")
        self.running = False

    def _create_socket(self, port):
        """Create and bind UDP socket for a port"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            sock.bind(('', port))
            sock.settimeout(1.0)  # 1 second timeout for checking self.running
            print(f"✅ Listening on port {port}")
            return sock
        except OSError as e:
            print(f"❌ Failed to bind to port {port}: {e}")
            print(f"   Port may already be in use. Stop other processes using port {port}.")
            return None

    def _open_recording_file(self, port):
        """Open a recording file for a specific port"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"rig_port{port}_{timestamp}.packets"

        # Create metadata
        metadata = {
            "version": "1.0",
            "recording_date": datetime.now().isoformat(),
            "port": port,
            "format": "Each packet: [timestamp(double)][size(uint32)][data(bytes)]"
        }

        # Write metadata as JSON header
        file_handle = open(filename, 'wb')
        metadata_json = json.dumps(metadata).encode('utf-8')
        file_handle.write(struct.pack('<I', len(metadata_json)))
        file_handle.write(metadata_json)

        print(f"📝 Recording port {port} to: {filename}")
        return file_handle, filename

    def _record_port(self, port):
        """Record packets from a specific port (runs in separate thread)"""
        sock = self._create_socket(port)
        if not sock:
            return

        file_handle, filename = self._open_recording_file(port)
        self.sockets[port] = sock
        self.files[port] = (file_handle, filename)

        try:
            while self.running:
                try:
                    data, addr = sock.recvfrom(2048)
                    timestamp = time.time()

                    # Write: timestamp (double) + size (uint32) + data (bytes)
                    file_handle.write(struct.pack('<d', timestamp))
                    file_handle.write(struct.pack('<I', len(data)))
                    file_handle.write(data)

                    self.packet_counts[port] += 1

                except socket.timeout:
                    # Normal timeout, check if we should continue
                    continue
                except Exception as e:
                    if self.running:
                        print(f"❌ Error recording port {port}: {e}")
                    break

        finally:
            file_handle.close()
            sock.close()
            print(f"💾 Saved port {port} recording: {filename}")

    def start(self):
        """Start recording from all ports"""
        print(f"\n🎬 Starting multi-rig recording")
        print(f"📂 Output directory: {self.output_dir.absolute()}")
        print(f"🔌 Ports: {', '.join(map(str, self.ports))}")
        print(f"\n⏱️  Recording started at {datetime.now().strftime('%H:%M:%S')}")
        print("Press Ctrl+C to stop recording\n")

        # Start a thread for each port
        for port in self.ports:
            thread = threading.Thread(target=self._record_port, args=(port,), daemon=True)
            thread.start()
            self.threads[port] = thread

        # Monitor and display stats
        last_update = time.time()
        try:
            while self.running:
                time.sleep(0.1)

                # Update stats every second
                if time.time() - last_update >= 1.0:
                    self._display_stats()
                    last_update = time.time()

        except KeyboardInterrupt:
            pass

        # Wait for all threads to finish
        print("\n⏳ Waiting for threads to finish...")
        for port, thread in self.threads.items():
            thread.join(timeout=2.0)

        # Final stats
        print("\n" + "="*60)
        self._display_final_stats()
        print("="*60)

    def _display_stats(self):
        """Display current recording statistics"""
        duration = time.time() - self.start_time
        total_packets = sum(self.packet_counts.values())

        stats = f"\r⏱️  {duration:.1f}s | "
        stats += " | ".join([
            f"Port {port}: {count:,} pkts"
            for port, count in sorted(self.packet_counts.items())
        ])
        stats += f" | Total: {total_packets:,}"

        sys.stdout.write(stats)
        sys.stdout.flush()

    def _display_final_stats(self):
        """Display final recording statistics"""
        duration = time.time() - self.start_time
        total_packets = sum(self.packet_counts.values())

        print(f"\n✅ Recording completed!")
        print(f"\n📊 Statistics:")
        print(f"   Duration: {duration:.1f} seconds")
        print(f"   Total packets: {total_packets:,}")

        for port, count in sorted(self.packet_counts.items()):
            rate = count / duration if duration > 0 else 0
            print(f"   Port {port}: {count:,} packets ({rate:.1f} pkts/sec)")

        print(f"\n📁 Recordings saved to: {self.output_dir.absolute()}")
        for port, (_, filename) in sorted(self.files.items()):
            file_size = filename.stat().st_size / (1024 * 1024)  # MB
            print(f"   {filename.name} ({file_size:.2f} MB)")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 record_all_rigs.py <output_directory> [port1] [port2] ...")
        print("\nExamples:")
        print("  # Record from default ports (20777, 20778)")
        print("  python3 record_all_rigs.py recordings/lan_session")
        print("\n  # Record from custom ports")
        print("  python3 record_all_rigs.py recordings/custom 20777 20778 20779")
        sys.exit(1)

    output_dir = sys.argv[1]

    # Parse ports or use defaults
    if len(sys.argv) > 2:
        ports = [int(p) for p in sys.argv[2:]]
    else:
        # Default to RIG A and RIG B ports
        ports = [20777, 20778]

    recorder = MultiRigRecorder(output_dir, ports)
    recorder.start()

if __name__ == "__main__":
    main()
