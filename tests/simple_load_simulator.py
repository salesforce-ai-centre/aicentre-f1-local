#!/usr/bin/env python3
"""
Simple F1 Load Simulator
A simplified version that generates basic UDP traffic for performance testing
"""

import socket
import time
import threading
import argparse
import logging
import random
import sys

class SimpleLoadSimulator:
    """Simple UDP load generator for performance testing"""
    
    def __init__(self, host="127.0.0.1", port=20777, pps=60, duration=300):
        self.host = host
        self.port = port
        self.packets_per_second = pps
        self.duration = duration
        self.packets_sent = 0
        self.running = False
        self.start_time = 0
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def create_simple_packet(self, packet_id=1):
        """Create a simple test packet"""
        # Create a basic packet with some realistic data
        data = bytearray(1024)  # 1KB packet
        
        # Add some header-like data
        data[0:4] = packet_id.to_bytes(4, 'little')  # Packet ID
        data[4:8] = int(time.time()).to_bytes(4, 'little')  # Timestamp
        data[8:12] = self.packets_sent.to_bytes(4, 'little')  # Sequence number
        
        # Fill with some random data to simulate telemetry
        for i in range(12, len(data)):
            data[i] = random.randint(0, 255)
        
        return bytes(data)
    
    def run_simulation(self):
        """Run the load simulation"""
        self.logger.info(f"Starting simple load simulation...")
        self.logger.info(f"Target: {self.host}:{self.port}")
        self.logger.info(f"Rate: {self.packets_per_second} packets/sec")
        self.logger.info(f"Duration: {self.duration} seconds")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.running = True
            self.start_time = time.time()
            
            packet_interval = 1.0 / self.packets_per_second
            next_packet_time = time.time()
            
            while self.running and (time.time() - self.start_time) < self.duration:
                current_time = time.time()
                
                if current_time >= next_packet_time:
                    # Create and send packet
                    packet = self.create_simple_packet()
                    
                    try:
                        sock.sendto(packet, (self.host, self.port))
                        self.packets_sent += 1
                    except Exception as e:
                        self.logger.error(f"Error sending packet: {e}")
                    
                    next_packet_time += packet_interval
                    
                    # Log progress every 1000 packets
                    if self.packets_sent % 1000 == 0:
                        elapsed = time.time() - self.start_time
                        rate = self.packets_sent / elapsed if elapsed > 0 else 0
                        self.logger.info(f"Sent {self.packets_sent} packets in {elapsed:.1f}s ({rate:.1f} pps)")
                
                # Small sleep to prevent CPU spinning
                time.sleep(0.001)
                
        except KeyboardInterrupt:
            self.logger.info("Simulation interrupted by user")
        except Exception as e:
            self.logger.error(f"Simulation error: {e}")
        finally:
            self.running = False
            if 'sock' in locals():
                sock.close()
            
            # Final statistics
            elapsed = time.time() - self.start_time
            avg_rate = self.packets_sent / elapsed if elapsed > 0 else 0
            self.logger.info(f"Simulation completed:")
            self.logger.info(f"  Total packets sent: {self.packets_sent}")
            self.logger.info(f"  Duration: {elapsed:.1f} seconds")
            self.logger.info(f"  Average rate: {avg_rate:.1f} packets/sec")

def main():
    parser = argparse.ArgumentParser(description='Simple F1 Load Simulator')
    parser.add_argument('--host', default='127.0.0.1', help='Target host')
    parser.add_argument('--port', type=int, default=20777, help='Target port')
    parser.add_argument('--pps', type=float, default=60.0, help='Packets per second')
    parser.add_argument('--duration', type=int, default=300, help='Duration in seconds')
    parser.add_argument('--stress', action='store_true', help='Enable stress mode (3x rate)')
    
    args = parser.parse_args()
    
    # Apply stress mode multiplier
    pps = args.pps * 3 if args.stress else args.pps
    
    simulator = SimpleLoadSimulator(
        host=args.host,
        port=args.port,
        pps=pps,
        duration=args.duration
    )
    
    simulator.run_simulation()

if __name__ == "__main__":
    main()