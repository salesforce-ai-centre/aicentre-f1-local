#!/usr/bin/env python3
"""
F1 Dashboard Performance Test Runner
Automated test runner that combines all performance testing tools
"""

import subprocess
import time
import sys
import argparse
import os
import signal
import threading
from datetime import datetime

class PerformanceTestRunner:
    def __init__(self):
        self.processes = []
        self.test_start_time = None
        
    def start_process(self, cmd, name, log_file=None):
        """Start a process and track it"""
        try:
            if log_file:
                with open(log_file, 'w') as f:
                    process = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, shell=True)
            else:
                process = subprocess.Popen(cmd, shell=True)
            
            self.processes.append((process, name))
            print(f"✅ Started {name} (PID: {process.pid})")
            return process
        except Exception as e:
            print(f"❌ Failed to start {name}: {e}")
            return None
    
    def stop_all_processes(self):
        """Stop all tracked processes"""
        for process, name in self.processes:
            try:
                process.terminate()
                print(f"🛑 Stopped {name}")
            except:
                pass
        
        # Wait for graceful shutdown
        time.sleep(2)
        
        # Force kill if needed
        for process, name in self.processes:
            try:
                if process.poll() is None:
                    process.kill()
                    print(f"🔴 Force killed {name}")
            except:
                pass
    
    def run_basic_test(self, duration=300):
        """Run basic performance test"""
        print(f"\n🚀 Starting Basic Performance Test ({duration}s)")
        print("=" * 60)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Ensure logs directory exists
            os.makedirs("logs", exist_ok=True)
            
            # Start performance monitor
            monitor_cmd = f"python3 performance_monitor.py --duration {duration} --output logs/basic_test_{timestamp}.jsonl"
            self.start_process(monitor_cmd, "Performance Monitor", f"logs/monitor_{timestamp}.log")
            
            # Wait a bit for monitor to start
            time.sleep(2)
            
            # Start simple load simulator (more reliable)
            simulator_cmd = f"python3 simple_load_simulator.py --duration {duration}"
            self.start_process(simulator_cmd, "Load Simulator", f"logs/simulator_{timestamp}.log")
            
            print(f"\n⏱️  Test running for {duration} seconds...")
            print("   - Monitor dashboard in your browser")
            print("   - Watch for performance warnings")
            print("   - Press Ctrl+C to stop early")
            
            # Wait for test completion
            time.sleep(duration + 10)  # Extra time for cleanup
            
        except KeyboardInterrupt:
            print("\n⚠️  Test interrupted by user")
        except Exception as e:
            print(f"\n❌ Test error: {e}")
        finally:
            self.stop_all_processes()
            print(f"\n📊 Test completed. Check logs/basic_test_{timestamp}.jsonl for results")
    
    def run_stress_test(self, duration=600):
        """Run stress test"""
        print(f"\n🔥 Starting Stress Test ({duration}s)")
        print("=" * 60)
        print("⚠️  This test will generate high CPU/memory load")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Ensure logs directory exists
            os.makedirs("logs", exist_ok=True)
            
            # Start intensive performance monitor
            monitor_cmd = f"python3 performance_monitor.py --interval 0.5 --duration {duration} --output logs/stress_test_{timestamp}.jsonl"
            self.start_process(monitor_cmd, "Performance Monitor", f"logs/stress_monitor_{timestamp}.log")
            
            time.sleep(2)
            
            # Start stress load simulator
            simulator_cmd = f"python3 simple_load_simulator.py --stress --duration {duration} --pps 150"
            self.start_process(simulator_cmd, "Stress Simulator", f"logs/stress_simulator_{timestamp}.log")
            
            print(f"\n⏱️  Stress test running for {duration} seconds...")
            print("   - Monitor system resources closely")
            print("   - Watch for performance degradation")
            print("   - Press Ctrl+C if system becomes unresponsive")
            
            # Wait for test completion
            time.sleep(duration + 10)
            
        except KeyboardInterrupt:
            print("\n⚠️  Stress test interrupted by user")
        except Exception as e:
            print(f"\n❌ Stress test error: {e}")
        finally:
            self.stop_all_processes()
            print(f"\n📊 Stress test completed. Check logs/stress_test_{timestamp}.jsonl for results")
    
    def run_endurance_test(self, duration=3600):
        """Run endurance test for memory leaks"""
        print(f"\n🏃 Starting Endurance Test ({duration}s / {duration//60} minutes)")
        print("=" * 60)
        print("🔍 This test checks for memory leaks and long-term stability")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Start long-term performance monitor
            monitor_cmd = f"python3 performance_monitor.py --interval 5.0 --duration {duration} --output endurance_test_{timestamp}.jsonl"
            self.start_process(monitor_cmd, "Performance Monitor", f"endurance_monitor_{timestamp}.log")
            
            time.sleep(2)
            
            # Start normal load simulator for extended period
            simulator_cmd = f"python3 load_test_simulator.py --duration {duration}"
            self.start_process(simulator_cmd, "Endurance Simulator", f"endurance_simulator_{timestamp}.log")
            
            print(f"\n⏱️  Endurance test running for {duration//60} minutes...")
            print("   - Monitoring for memory leaks")
            print("   - Checking long-term stability")
            print("   - This test can be safely interrupted")
            
            # Periodic progress updates
            start_time = time.time()
            while time.time() - start_time < duration:
                time.sleep(300)  # Update every 5 minutes
                elapsed = time.time() - start_time
                remaining = duration - elapsed
                print(f"   ⏱️  Progress: {elapsed//60:.0f}/{duration//60} minutes ({remaining//60:.0f} minutes remaining)")
            
        except KeyboardInterrupt:
            print("\n⚠️  Endurance test interrupted by user")
        except Exception as e:
            print(f"\n❌ Endurance test error: {e}")
        finally:
            self.stop_all_processes()
            print(f"\n📊 Endurance test completed. Check endurance_test_{timestamp}.jsonl for results")
    
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        try:
            import psutil
            print("✅ Performance monitoring dependencies available")
            return True
        except ImportError:
            print("❌ Missing dependencies. Run: python install_performance_deps.py")
            return False

def main():
    parser = argparse.ArgumentParser(description='F1 Dashboard Performance Test Runner')
    parser.add_argument('--test', choices=['basic', 'stress', 'endurance'], 
                       default='basic', help='Test type to run')
    parser.add_argument('--duration', type=int, default=None,
                       help='Test duration in seconds (overrides defaults)')
    parser.add_argument('--check-deps', action='store_true',
                       help='Check dependencies and exit')
    
    args = parser.parse_args()
    
    runner = PerformanceTestRunner()
    
    # Check dependencies
    if args.check_deps or not runner.check_dependencies():
        if args.check_deps:
            sys.exit(0)
        else:
            sys.exit(1)
    
    # Set up signal handler for clean shutdown
    def signal_handler(sig, frame):
        print('\n🛑 Received interrupt signal, stopping tests...')
        runner.stop_all_processes()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run the specified test
    try:
        if args.test == 'basic':
            duration = args.duration or 300
            runner.run_basic_test(duration)
        elif args.test == 'stress':
            duration = args.duration or 600
            runner.run_stress_test(duration)
        elif args.test == 'endurance':
            duration = args.duration or 3600
            runner.run_endurance_test(duration)
    except Exception as e:
        print(f"❌ Test runner error: {e}")
        runner.stop_all_processes()
        sys.exit(1)

if __name__ == "__main__":
    main()