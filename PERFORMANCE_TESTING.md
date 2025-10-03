# F1 Dashboard Performance Testing Guide

This document provides comprehensive guidance for testing and monitoring the performance of the F1 telemetry dashboard to ensure it runs efficiently without consuming excessive system resources.

## Overview

The F1 dashboard consists of several components that need performance monitoring:
- **UDP Receiver** (`receiver.py`) - Processes F1 telemetry data
- **Flask Web Server** (`app.py`) - Serves the dashboard and handles SSE
- **Web Browser** - Renders the dashboard with real-time charts
- **Data Cloud Integration** (optional) - Sends data to Salesforce Data Cloud

## Performance Testing Tools

### 1. Performance Monitor (`performance_monitor.py`)

Real-time monitoring of system resources used by F1 dashboard components.

#### Usage:
```bash
# Basic monitoring
python performance_monitor.py

# Monitor for specific duration with data logging
python performance_monitor.py --duration 300 --output performance_data.jsonl

# High-frequency monitoring (every 0.5 seconds)
python performance_monitor.py --interval 0.5

# Monitor with detailed logging
python performance_monitor.py --duration 600 --output detailed_performance.jsonl
```

#### What it monitors:
- **CPU Usage**: Per-process and system-wide CPU utilization
- **Memory Usage**: RAM consumption in MB and percentage
- **Thread Count**: Number of active threads per process
- **I/O Operations**: Disk read/write and network traffic
- **Process Status**: Running state and resource handles

#### Sample Output:
```
============ F1 DASHBOARD PERFORMANCE REPORT ============

Monitoring Duration: 300.0 seconds
Data Points Collected: 300

SYSTEM PERFORMANCE:
  CPU Usage: 12.3% avg, 25.1% max
  Memory Usage: 45.2% avg, 47.8% max

IMPACT ON SYSTEM:
  CPU Increase: +3.2%
  Memory Increase: +2.1%

PROCESS BREAKDOWN:
  UDP_Receiver:
    CPU: 2.1% avg, 8.5% max
    Memory: 45MB avg, 52MB max
  Flask_App:
    CPU: 1.8% avg, 4.2% max
    Memory: 78MB avg, 85MB max
```

### 2. Enhanced Receiver Logging

The receiver now includes built-in performance metrics in its status updates.

#### Performance Metrics Logged:
```
Process: CPU 2.1% | Memory 45MB (1.2%) | Threads 3
System:  CPU 12.3% | Memory 45.2%
```

### 3. Load Testing Simulator (`load_test_simulator.py`)

Simulates high-frequency F1 telemetry data to stress-test the dashboard.

#### Usage:
```bash
# Normal load test (60 packets/second for 5 minutes)
python load_test_simulator.py

# Stress test (3x normal packet rate)
python load_test_simulator.py --stress --duration 180

# High-frequency test
python load_test_simulator.py --pps 120 --duration 600

# Custom test parameters
python load_test_simulator.py --host 127.0.0.1 --port 20777 --pps 90 --cars 22
```

#### Test Scenarios:
- **Normal Load**: 60 packets/second (simulates real F1 game)
- **Stress Test**: 180+ packets/second (3x normal rate)
- **Extended Test**: Long-duration testing (10+ minutes)
- **Variable Load**: Random packet timing variations

## Performance Testing Procedures

### Pre-Test Setup

1. **Close unnecessary applications** to get baseline measurements
2. **Ensure stable system state** (no background updates, etc.)
3. **Check available system resources**:
   ```bash
   # Check system resources
   htop  # or top on older systems
   free -h  # Memory usage
   df -h   # Disk space
   ```

### Test Procedure 1: Baseline Performance Test

**Objective**: Establish normal resource usage patterns

1. **Start Performance Monitor**:
   ```bash
   python performance_monitor.py --duration 300 --output baseline_test.jsonl
   ```

2. **Start F1 Dashboard**:
   ```bash
   # Terminal 1: Start the receiver
   python receiver.py --driver "Test Driver" --track "Silverstone"
   
   # Terminal 2: Start the web app
   python run_dashboard.py
   ```

3. **Run Normal Load Simulation**:
   ```bash
   # Terminal 3: Start load simulator
   python load_test_simulator.py --duration 300
   ```

4. **Monitor and Record**: Let the test run for 5 minutes, monitoring system performance

### Test Procedure 2: Stress Test

**Objective**: Test system behavior under high load

1. **Start Enhanced Monitoring**:
   ```bash
   python performance_monitor.py --interval 0.5 --duration 600 --output stress_test.jsonl
   ```

2. **Start Dashboard Components** (same as above)

3. **Run Stress Load Simulation**:
   ```bash
   python load_test_simulator.py --stress --duration 600 --pps 150
   ```

4. **Monitor for Issues**: Watch for CPU spikes, memory leaks, or performance degradation

### Test Procedure 3: Extended Endurance Test

**Objective**: Test for memory leaks and long-term stability

1. **Start Long-term Monitoring**:
   ```bash
   python performance_monitor.py --duration 3600 --output endurance_test.jsonl
   ```

2. **Run Extended Load Test**:
   ```bash
   python load_test_simulator.py --duration 3600 --pps 60
   ```

3. **Monitor Memory Growth**: Check for gradual memory increase over time

## Performance Benchmarks

### Expected Performance Ranges

#### Normal Operation (60 packets/second):
- **UDP Receiver**: 1-3% CPU, 30-50MB RAM
- **Flask App**: 1-2% CPU, 50-80MB RAM
- **Total System Impact**: +2-5% CPU, +100-150MB RAM

#### Stress Test (180+ packets/second):
- **UDP Receiver**: 3-8% CPU, 40-60MB RAM
- **Flask App**: 2-5% CPU, 60-100MB RAM
- **Total System Impact**: +5-12% CPU, +150-200MB RAM

### Warning Thresholds

- **CPU Usage**: >15% sustained CPU usage per process
- **Memory Usage**: >200MB RAM per process
- **Memory Growth**: >10MB/hour memory increase (indicates leak)
- **Response Time**: >100ms average API response time
- **Packet Loss**: >1% packet processing failures

## Performance Optimization Guidelines

### 1. System-Level Optimizations

```bash
# Increase UDP buffer sizes (Linux/macOS)
sudo sysctl -w net.core.rmem_max=134217728
sudo sysctl -w net.core.rmem_default=134217728

# Set process priorities (if needed)
sudo renice -10 $(pgrep -f receiver.py)  # Higher priority for receiver
```

### 2. Application-Level Optimizations

#### receiver.py optimizations:
- **Reduce send interval**: Default 0.01s (10ms) - increase if CPU usage is high
- **Batch processing**: Group multiple packets before sending to API
- **Disable debug logging**: Set `debug=False` for production use

#### app.py optimizations:
- **SSE connection limits**: Monitor concurrent SSE connections
- **Data caching**: Implement caching for computed values
- **Chart update frequency**: Reduce chart update frequency if needed

### 3. Browser Optimizations

- **Close other tabs**: Reduce browser memory usage
- **Disable extensions**: Temporarily disable browser extensions
- **Use Chrome/Edge**: Generally better performance than Firefox for canvas rendering

## Troubleshooting Performance Issues

### High CPU Usage

**Symptoms**: CPU usage >20% sustained
**Causes**: 
- Too high packet frequency
- Complex chart calculations
- Memory garbage collection

**Solutions**:
```bash
# Reduce packet frequency
python receiver.py --send-interval 0.02  # 20ms instead of 10ms

# Monitor with lower frequency
python performance_monitor.py --interval 2.0
```

### High Memory Usage

**Symptoms**: Memory usage >500MB total
**Causes**:
- Memory leaks in chart libraries
- Accumulated telemetry data
- Large SSE message queues

**Solutions**:
- Restart dashboard components periodically
- Implement data cleanup in charts
- Monitor browser memory usage

### Poor Dashboard Responsiveness

**Symptoms**: Laggy chart updates, delayed data
**Causes**:
- Network latency
- Browser performance issues
- High system load

**Solutions**:
- Use local deployment (avoid remote URLs)
- Reduce chart animation complexity
- Close unnecessary applications

## Data Analysis

### Analyzing Performance Logs

```bash
# Extract CPU usage trends
grep "CPU" performance_data.jsonl | jq '.processes.UDP_Receiver.cpu_percent'

# Calculate average memory usage
grep "memory_rss_mb" performance_data.jsonl | jq '.processes.UDP_Receiver.memory_rss_mb' | awk '{sum+=$1; count++} END {print sum/count}'

# Find peak resource usage
jq '.system.cpu_percent' performance_data.jsonl | sort -n | tail -5
```

### Performance Report Generation

The performance monitor automatically generates reports. Key metrics to track:
- **Average Resource Usage**: Baseline performance indicators
- **Peak Resource Usage**: Maximum system impact
- **Resource Growth Rate**: Detecting memory leaks
- **System Impact**: Overall effect on system performance

## Continuous Monitoring

### Production Monitoring Setup

1. **Add system monitoring**:
   ```bash
   # Add to crontab for periodic monitoring
   */15 * * * * /usr/bin/python3 /path/to/performance_monitor.py --duration 60 --output /var/log/f1_performance.log
   ```

2. **Log rotation**:
   ```bash
   # Add to logrotate configuration
   /var/log/f1_performance.log {
       daily
       rotate 7
       compress
       missingok
       notifempty
   }
   ```

3. **Alert thresholds**: Set up alerts for performance degradation

## Hardware Recommendations

### Minimum Requirements:
- **CPU**: 2+ cores, 2GHz+
- **RAM**: 4GB available
- **Network**: 100Mbps+ for remote deployment
- **Storage**: 1GB free space for logs

### Recommended Specifications:
- **CPU**: 4+ cores, 3GHz+
- **RAM**: 8GB+ available
- **Network**: 1Gbps for high-frequency telemetry
- **Storage**: 10GB+ for extended logging

## Conclusion

Regular performance testing ensures the F1 dashboard remains responsive and efficient. Use the provided tools to establish baselines, identify bottlenecks, and optimize resource usage for the best user experience.

For questions or issues with performance testing, refer to the troubleshooting section or check the application logs for detailed error information.