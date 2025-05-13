#!/usr/bin/env python3
"""
F1 Dashboard Launcher
Starts both the Flask web server and the telemetry receiver in a single command.
"""

import os
import sys
import argparse
import subprocess
import threading
import time
import webbrowser

def start_flask_server(debug=False):
    """Start the Flask web server that hosts the dashboard."""
    print("Starting F1 Dashboard web server...")
    flask_env = os.environ.copy()
    
    if debug:
        cmd = ["flask", "run", "--debug", "--host", "0.0.0.0"]
    else:
        cmd = [sys.executable, "app.py"]  # Use the built-in app.run() in app.py
    
    # Return the process so we can terminate it later
    return subprocess.Popen(
        cmd,
        env=flask_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )

def start_receiver(driver_name, track_name, server_url, debug=False, server_port=8080):
    """Start the telemetry receiver that connects to the F1 game."""
    print(f"Starting telemetry receiver for driver '{driver_name}' on '{track_name}'...")
    
    cmd = [
        sys.executable, "receiver.py",
        "--driver", driver_name,
        "--track", track_name,
        "--url", server_url,
        "--server-port", str(server_port),
    ]
    
    if debug:
        cmd.append("--debug")
    
    # Return the process so we can terminate it later
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )

def log_output(process, prefix, debug=False):
    """Read and print output from a subprocess with a prefix, filtering for useful info."""
    for line in iter(process.stdout.readline, ""):
        if not line:
            continue
            
        line_text = line.strip()
        
        # Always show errors and important status updates
        if any(x in line_text for x in [
            "[ERROR", "[CRITICAL", 
            "Status update", "Uptime:", "Connected", 
            "Circuit", "Team:", "Lap:", "Starting", 
            "Initialized", "Position:", "Fastest lap"
        ]):
            print(f"{prefix}: {line_text}")
        # Show detailed logs if debug mode is enabled
        elif debug and ("[DEBUG" in line_text or "[INFO" in line_text):
            print(f"{prefix}: {line_text}")
        # Filter out common noise
        elif not any(x in line_text for x in [
            "Send success", "127.0.0.1", "Sending Payload", "POST /data"
        ]):
            # Show other important info that doesn't match the patterns above
            print(f"{prefix}: {line_text}")
    
    # If we get here, the process has ended
    if process.poll() is None:
        process.terminate()

def open_browser(url, delay=2):
    """Open the dashboard in a web browser after a short delay."""
    time.sleep(delay)  # Give the server time to start
    print(f"Opening dashboard in web browser: {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start F1 Dashboard components with a single command")
    parser.add_argument("--driver", type=str, default="Guest Driver", help="Driver name to display on dashboard")
    parser.add_argument("--track", type=str, default="Unknown Track", help="Track name to display on dashboard")
    parser.add_argument("--port", type=int, default=8080, help="Port for the web server (default: 8080)")
    parser.add_argument("--no-browser", action="store_true", help="Don't automatically open web browser")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode for more verbose logging")
    args = parser.parse_args()

    # Set the server URL based on the port
    server_url = f"http://localhost:{args.port}/data"
    dashboard_url = f"http://localhost:{args.port}"
    
    # Set PORT environment variable for Flask
    os.environ["PORT"] = str(args.port)
    
    try:
        # Start the Flask web server
        flask_process = start_flask_server(args.debug)
        
        # Start a thread to monitor and log its output (with debug flag)
        flask_thread = threading.Thread(
            target=log_output,
            args=(flask_process, "DASHBOARD", args.debug),
            daemon=True
        )
        flask_thread.start()
        
        # Give the server a moment to start up
        time.sleep(1)
        
        # Start the telemetry receiver
        receiver_process = start_receiver(
            driver_name=args.driver,
            track_name=args.track,
            server_url=server_url,
            debug=args.debug,
            server_port=args.port
        )
        
        # Start a thread to monitor and log its output (with debug flag)
        receiver_thread = threading.Thread(
            target=log_output,
            args=(receiver_process, "RECEIVER", args.debug),
            daemon=True
        )
        receiver_thread.start()
        
        # Open the dashboard in a web browser if requested
        if not args.no_browser:
            browser_thread = threading.Thread(
                target=open_browser,
                args=(dashboard_url,),
                daemon=True
            )
            browser_thread.start()
        
        print(f"\nF1 Dashboard is running!")
        print(f"Dashboard URL: {dashboard_url}")
        print(f"Telemetry receiver is listening for F1 game data")
        print("\nPress Ctrl+C to stop all components\n")
        
        # Wait for processes to complete or user interrupt
        while True:
            # Check if processes are still running
            if flask_process.poll() is not None:
                print("Dashboard server has stopped.")
                break
            if receiver_process.poll() is not None:
                print("Telemetry receiver has stopped.")
                break
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nShutdown requested. Stopping all components...")
    finally:
        # Clean shutdown of all processes
        # Define empty process variables in case they weren't initialized
        if 'flask_process' not in locals():
            flask_process = None
        if 'receiver_process' not in locals():
            receiver_process = None
            
        for process in [p for p in [flask_process, receiver_process] if p and p.poll() is None]:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()  # Force kill if it doesn't terminate
        
        print("F1 Dashboard shutdown complete.")