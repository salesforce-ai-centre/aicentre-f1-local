#!/usr/bin/env python3
"""
Simple test script to verify performance monitoring tools work correctly
"""

import subprocess
import time
import sys
import os

def test_performance_monitor():
    """Test the performance monitor directly"""
    print("🔍 Testing Performance Monitor...")
    
    try:
        # Run performance monitor for 10 seconds
        result = subprocess.run([
            sys.executable, "performance_monitor.py", 
            "--duration", "10",
            "--output", "test_monitor_output.jsonl"
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            print("✅ Performance Monitor: SUCCESS")
            
            # Check if output file was created
            if os.path.exists("test_monitor_output.jsonl"):
                print("✅ Output file created successfully")
                
                # Show first few lines
                with open("test_monitor_output.jsonl", "r") as f:
                    lines = f.readlines()
                    print(f"📄 Generated {len(lines)} data points")
                    if lines:
                        print(f"📝 Sample data: {lines[0][:100]}...")
                
                # Clean up
                os.remove("test_monitor_output.jsonl")
            else:
                print("⚠️  Output file not created")
        else:
            print("❌ Performance Monitor: FAILED")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⚠️  Performance Monitor: TIMEOUT")
    except Exception as e:
        print(f"❌ Performance Monitor: ERROR - {e}")

def test_load_simulator():
    """Test the load simulator directly"""
    print("\n🔍 Testing Load Simulator...")
    
    try:
        # Run load simulator for 5 seconds
        result = subprocess.run([
            sys.executable, "load_test_simulator.py",
            "--duration", "5",
            "--pps", "30",  # Lower packet rate for quick test
            "--verbose"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Load Simulator: SUCCESS")
            print(f"📊 Output: {result.stdout.split('/')[-1] if result.stdout else 'No output'}")
        else:
            print("❌ Load Simulator: FAILED")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⚠️  Load Simulator: TIMEOUT")
    except Exception as e:
        print(f"❌ Load Simulator: ERROR - {e}")

def test_combined():
    """Test both tools together briefly"""
    print("\n🔍 Testing Combined Performance Test...")
    
    try:
        # Start performance monitor
        monitor_process = subprocess.Popen([
            sys.executable, "performance_monitor.py",
            "--duration", "15",
            "--output", "combined_test.jsonl"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment
        time.sleep(2)
        
        # Start load simulator
        simulator_process = subprocess.Popen([
            sys.executable, "load_test_simulator.py",
            "--duration", "10",
            "--pps", "20"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for simulator to finish
        simulator_stdout, simulator_stderr = simulator_process.communicate(timeout=15)
        
        # Wait for monitor to finish
        monitor_stdout, monitor_stderr = monitor_process.communicate(timeout=20)
        
        if simulator_process.returncode == 0 and monitor_process.returncode == 0:
            print("✅ Combined Test: SUCCESS")
            
            # Check output file
            if os.path.exists("combined_test.jsonl"):
                with open("combined_test.jsonl", "r") as f:
                    lines = f.readlines()
                    print(f"📄 Generated {len(lines)} monitoring data points")
                os.remove("combined_test.jsonl")
            
        else:
            print("❌ Combined Test: FAILED")
            if simulator_process.returncode != 0:
                print(f"Simulator error: {simulator_stderr.decode()}")
            if monitor_process.returncode != 0:
                print(f"Monitor error: {monitor_stderr.decode()}")
                
    except subprocess.TimeoutExpired:
        print("⚠️  Combined Test: TIMEOUT")
        # Clean up processes
        try:
            monitor_process.terminate()
            simulator_process.terminate()
        except:
            pass
    except Exception as e:
        print(f"❌ Combined Test: ERROR - {e}")

def check_dependencies():
    """Check if all required dependencies are available"""
    print("🔍 Checking Dependencies...")
    
    try:
        import psutil
        print("✅ psutil: Available")
    except ImportError:
        print("❌ psutil: Missing (run: pip install psutil)")
        return False
    
    # Check if performance scripts exist
    if os.path.exists("performance_monitor.py"):
        print("✅ performance_monitor.py: Found")
    else:
        print("❌ performance_monitor.py: Missing")
        return False
        
    if os.path.exists("load_test_simulator.py"):
        print("✅ load_test_simulator.py: Found")
    else:
        print("❌ load_test_simulator.py: Missing")
        return False
    
    return True

def main():
    print("F1 Dashboard Performance Tools Test")
    print("=" * 50)
    
    if not check_dependencies():
        print("\n❌ Missing dependencies. Please install them first.")
        return
    
    print("\n🚀 Starting tests...")
    
    # Test individual components
    test_performance_monitor()
    test_load_simulator()
    test_combined()
    
    print("\n" + "=" * 50)
    print("✅ Performance tools testing completed!")
    print("\nIf all tests passed, you can now run:")
    print("   python3 run_performance_test.py --test basic --duration 30")

if __name__ == "__main__":
    main()