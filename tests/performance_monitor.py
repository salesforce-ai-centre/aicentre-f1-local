#!/usr/bin/env python3
"""
F1 Dashboard Performance Monitor
Monitors system resources used by the F1 dashboard components
"""

import psutil
import time
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Optional
import threading
import subprocess
import sys

class PerformanceMonitor:
    def __init__(self, monitor_interval: float = 1.0, output_file: Optional[str] = None):
        self.monitor_interval = monitor_interval
        self.output_file = output_file
        self.monitoring = False
        self.data_points: List[Dict] = []
        
        # Process tracking
        self.tracked_processes: Dict[str, psutil.Process] = {}
        
        # System baseline
        self.baseline_cpu = None
        self.baseline_memory = None
        
        self.setup_logging()
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('performance_monitor.log') if self.output_file else logging.NullHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def find_f1_processes(self) -> Dict[str, psutil.Process]:
        """Find all F1 dashboard related processes"""
        processes = {}
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    
                    # Look for F1 dashboard related processes
                    if any(keyword in cmdline.lower() for keyword in [
                        'receiver.py', 'app.py', 'run_dashboard.py', 
                        'f1-telemetry', 'gunicorn', 'flask'
                    ]):
                        process_name = self.identify_process_type(cmdline)
                        processes[process_name] = psutil.Process(proc.info['pid'])
                        self.logger.info(f"Found F1 process: {process_name} (PID: {proc.info['pid']})")
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return processes
    
    def identify_process_type(self, cmdline: str) -> str:
        """Identify the type of F1 dashboard process"""
        cmdline_lower = cmdline.lower()
        
        if 'receiver.py' in cmdline_lower:
            return 'UDP_Receiver'
        elif 'app.py' in cmdline_lower or 'gunicorn' in cmdline_lower:
            return 'Flask_App'
        elif 'run_dashboard.py' in cmdline_lower:
            return 'Dashboard_Launcher'
        else:
            return 'F1_Related'
    
    def get_system_baseline(self):
        """Get baseline system performance before starting monitoring"""
        self.baseline_cpu = psutil.cpu_percent(interval=1)
        self.baseline_memory = psutil.virtual_memory().percent
        
        self.logger.info(f"System baseline - CPU: {self.baseline_cpu:.1f}%, Memory: {self.baseline_memory:.1f}%")
    
    def collect_performance_data(self) -> Dict:
        """Collect performance data for all tracked processes"""
        timestamp = datetime.now().isoformat()
        
        # System-wide metrics
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk_io = psutil.disk_io_counters()
        net_io = psutil.net_io_counters()
        
        data_point = {
            'timestamp': timestamp,
            'system': {
                'cpu_percent': cpu_percent,
                'cpu_count': psutil.cpu_count(),
                'memory_percent': memory.percent,
                'memory_used_mb': memory.used / (1024 * 1024),
                'memory_available_mb': memory.available / (1024 * 1024),
                'disk_read_mb': disk_io.read_bytes / (1024 * 1024) if disk_io else 0,
                'disk_write_mb': disk_io.write_bytes / (1024 * 1024) if disk_io else 0,
                'network_sent_mb': net_io.bytes_sent / (1024 * 1024) if net_io else 0,
                'network_recv_mb': net_io.bytes_recv / (1024 * 1024) if net_io else 0,
            },
            'processes': {}
        }
        
        # Process-specific metrics
        for proc_name, process in self.tracked_processes.items():
            try:
                # Check if process is still running
                if not process.is_running():
                    self.logger.warning(f"Process {proc_name} is no longer running")
                    continue
                
                with process.oneshot():
                    proc_data = {
                        'pid': process.pid,
                        'cpu_percent': process.cpu_percent(),
                        'memory_percent': process.memory_percent(),
                        'memory_rss_mb': process.memory_info().rss / (1024 * 1024),
                        'memory_vms_mb': process.memory_info().vms / (1024 * 1024),
                        'num_threads': process.num_threads(),
                        'num_fds': process.num_fds() if hasattr(process, 'num_fds') else 0,
                        'status': process.status(),
                        'create_time': process.create_time(),
                    }
                    
                    # Get I/O stats if available
                    try:
                        io_counters = process.io_counters()
                        proc_data.update({
                            'io_read_mb': io_counters.read_bytes / (1024 * 1024),
                            'io_write_mb': io_counters.write_bytes / (1024 * 1024),
                        })
                    except (psutil.AccessDenied, AttributeError):
                        proc_data.update({'io_read_mb': 0, 'io_write_mb': 0})
                
                data_point['processes'][proc_name] = proc_data
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                self.logger.warning(f"Error collecting data for {proc_name}: {e}")
                continue
        
        return data_point
    
    def monitor_loop(self):
        """Main monitoring loop"""
        self.logger.info(f"Starting performance monitoring (interval: {self.monitor_interval}s)")
        
        while self.monitoring:
            try:
                data_point = self.collect_performance_data()
                self.data_points.append(data_point)
                
                # Log current performance
                self.log_current_performance(data_point)
                
                # Write to file if specified
                if self.output_file:
                    self.write_data_point(data_point)
                
                time.sleep(self.monitor_interval)
                
            except KeyboardInterrupt:
                self.logger.info("Monitoring interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Error during monitoring: {e}")
                time.sleep(self.monitor_interval)
    
    def log_current_performance(self, data_point: Dict):
        """Log current performance metrics"""
        system = data_point['system']
        processes = data_point['processes']
        
        # System summary
        self.logger.info(f"System: CPU {system['cpu_percent']:.1f}%, "
                        f"Memory {system['memory_percent']:.1f}% "
                        f"({system['memory_used_mb']:.0f}MB used)")
        
        # Process summary
        for proc_name, proc_data in processes.items():
            self.logger.info(f"{proc_name}: CPU {proc_data['cpu_percent']:.1f}%, "
                           f"Memory {proc_data['memory_rss_mb']:.0f}MB, "
                           f"Threads {proc_data['num_threads']}")
    
    def write_data_point(self, data_point: Dict):
        """Write data point to output file"""
        try:
            with open(self.output_file, 'a') as f:
                f.write(json.dumps(data_point) + '\n')
        except Exception as e:
            self.logger.error(f"Error writing to output file: {e}")
    
    def start_monitoring(self):
        """Start the performance monitoring"""
        self.get_system_baseline()
        self.tracked_processes = self.find_f1_processes()
        
        if not self.tracked_processes:
            self.logger.warning("No F1 dashboard processes found! Monitoring system-wide performance only.")
            # Continue with system monitoring even if no F1 processes found
        
        self.monitoring = True
        monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        monitor_thread.start()
        
        return True
    
    def stop_monitoring(self):
        """Stop the performance monitoring"""
        self.monitoring = False
        self.logger.info("Performance monitoring stopped")
    
    def generate_report(self) -> Dict:
        """Generate a performance summary report"""
        if not self.data_points:
            return {"error": "No data points collected"}
        
        # Calculate statistics
        cpu_values = [dp['system']['cpu_percent'] for dp in self.data_points]
        memory_values = [dp['system']['memory_percent'] for dp in self.data_points]
        
        report = {
            'monitoring_duration_seconds': len(self.data_points) * self.monitor_interval,
            'data_points_collected': len(self.data_points),
            'system_performance': {
                'cpu_avg': sum(cpu_values) / len(cpu_values),
                'cpu_max': max(cpu_values),
                'cpu_min': min(cpu_values),
                'memory_avg': sum(memory_values) / len(memory_values),
                'memory_max': max(memory_values),
                'memory_min': min(memory_values),
            },
            'baseline_comparison': {
                'cpu_increase': (sum(cpu_values) / len(cpu_values)) - (self.baseline_cpu or 0),
                'memory_increase': (sum(memory_values) / len(memory_values)) - (self.baseline_memory or 0),
            },
            'process_performance': {}
        }
        
        # Process-specific statistics
        for proc_name in set(proc for dp in self.data_points for proc in dp['processes'].keys()):
            proc_cpu_values = []
            proc_memory_values = []
            
            for dp in self.data_points:
                if proc_name in dp['processes']:
                    proc_cpu_values.append(dp['processes'][proc_name]['cpu_percent'])
                    proc_memory_values.append(dp['processes'][proc_name]['memory_rss_mb'])
            
            if proc_cpu_values:
                report['process_performance'][proc_name] = {
                    'cpu_avg': sum(proc_cpu_values) / len(proc_cpu_values),
                    'cpu_max': max(proc_cpu_values),
                    'memory_avg_mb': sum(proc_memory_values) / len(proc_memory_values),
                    'memory_max_mb': max(proc_memory_values),
                    'data_points': len(proc_cpu_values)
                }
        
        return report
    
    def print_report(self):
        """Print a formatted performance report"""
        report = self.generate_report()
        
        if 'error' in report:
            print(f"Report Error: {report['error']}")
            return
        
        print("\n" + "="*60)
        print("F1 DASHBOARD PERFORMANCE REPORT")
        print("="*60)
        
        print(f"\nMonitoring Duration: {report['monitoring_duration_seconds']:.1f} seconds")
        print(f"Data Points Collected: {report['data_points_collected']}")
        
        print(f"\nSYSTEM PERFORMANCE:")
        sys_perf = report['system_performance']
        print(f"  CPU Usage: {sys_perf['cpu_avg']:.1f}% avg, {sys_perf['cpu_max']:.1f}% max")
        print(f"  Memory Usage: {sys_perf['memory_avg']:.1f}% avg, {sys_perf['memory_max']:.1f}% max")
        
        baseline = report['baseline_comparison']
        print(f"\nIMPACT ON SYSTEM:")
        print(f"  CPU Increase: {baseline['cpu_increase']:+.1f}%")
        print(f"  Memory Increase: {baseline['memory_increase']:+.1f}%")
        
        print(f"\nPROCESS BREAKDOWN:")
        for proc_name, proc_stats in report['process_performance'].items():
            print(f"  {proc_name}:")
            print(f"    CPU: {proc_stats['cpu_avg']:.1f}% avg, {proc_stats['cpu_max']:.1f}% max")
            print(f"    Memory: {proc_stats['memory_avg_mb']:.0f}MB avg, {proc_stats['memory_max_mb']:.0f}MB max")
        
        print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(description='Monitor F1 Dashboard Performance')
    parser.add_argument('--interval', type=float, default=1.0, 
                       help='Monitoring interval in seconds (default: 1.0)')
    parser.add_argument('--output', type=str, 
                       help='Output file for detailed data (JSON lines format)')
    parser.add_argument('--duration', type=int, default=0,
                       help='Monitoring duration in seconds (0 = run until interrupted)')
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor(
        monitor_interval=args.interval,
        output_file=args.output
    )
    
    if not monitor.start_monitoring():
        sys.exit(1)
    
    try:
        if args.duration > 0:
            print(f"Monitoring for {args.duration} seconds...")
            time.sleep(args.duration)
        else:
            print("Monitoring until interrupted (Ctrl+C)...")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping monitoring...")
    
    monitor.stop_monitoring()
    time.sleep(1)  # Allow final data collection
    
    monitor.print_report()
    
    if args.output:
        print(f"\nDetailed data written to: {args.output}")


if __name__ == "__main__":
    main()