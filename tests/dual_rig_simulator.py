#!/usr/bin/env python3
"""
Dual Rig F1 Telemetry Simulator
Simulates telemetry data for both RIG_A and RIG_B for testing the dashboard
"""

import socketio
import time
import random
import sys

# Connect to the telemetry gateway
sio = socketio.Client()

@sio.event
def connect():
    print("✓ Connected to telemetry gateway")

@sio.event
def disconnect():
    print("✗ Disconnected from gateway")

def generate_lap_time():
    """Generate a realistic lap time (between 75-95 seconds)"""
    base_time = random.uniform(75000, 95000)  # milliseconds
    return int(base_time)

def simulate_rig_data(rig_id, lap_num, session_uid):
    """Generate simulated telemetry data for a rig"""
    # Generate lap time that gets progressively faster (simulating improvement)
    base_time = 85000 - (lap_num * random.uniform(200, 800))  # Get faster each lap
    lap_time = max(int(base_time + random.uniform(-1000, 1000)), 72000)  # Min 1:12

    return {
        'rig_id': rig_id,
        'sessionUID': session_uid,
        'overallFrameIdentifier': lap_num * 1000 + random.randint(0, 999),
        'trackName': 'Silverstone',
        'sessionTypeName': 'Time Trial',

        # Speed and gear
        'speed': random.randint(200, 320),
        'gear': random.randint(5, 8),
        'engineRPM': random.randint(10000, 13500),

        # Inputs
        'throttle': random.uniform(0.6, 1.0),
        'brake': random.uniform(0, 0.3),
        'steer': random.uniform(-0.5, 0.5),

        # G-Forces
        'gForceLateral': random.uniform(-2.5, 2.5),
        'gForceLongitudinal': random.uniform(-3.0, 1.5),
        'gForceVertical': random.uniform(-1.0, 1.0),

        # Tyre temps (FL, FR, RL, RR)
        'tyresSurfaceTemperature': [
            random.randint(85, 105),
            random.randint(85, 105),
            random.randint(85, 105),
            random.randint(85, 105)
        ],

        # Position and lap
        'carPosition': random.randint(1, 5),
        'currentLapNum': lap_num,
        'currentLapTimeInMS': random.randint(30000, 90000),
        'lastLapTimeInMS': lap_time if lap_num > 1 else 0,
        'currentLapInvalid': False,

        # DRS
        'drsActivation': random.randint(0, 2),  # 0=off, 1=available, 2=active
        'drsDistance': random.uniform(0, 1.0),

        # Fuel
        'fuelInTank': random.uniform(15.0, 30.0),
        'fuelRemainingLaps': random.uniform(8.0, 15.0),

        # ERS
        'ersStoreEnergy': random.uniform(1.5, 4.0),
        'ersDeployMode': random.randint(0, 3),

        # Tyre wear
        'tyresWear': [
            random.uniform(10.0, 40.0),
            random.uniform(10.0, 40.0),
            random.uniform(10.0, 40.0),
            random.uniform(10.0, 40.0)
        ]
    }

def run_simulation():
    """Run the dual rig simulation"""
    try:
        # Connect to the gateway
        print("Connecting to telemetry gateway on http://localhost:8080...")
        sio.connect('http://localhost:8080')

        print("\n" + "="*60)
        print("DUAL RIG SIMULATOR STARTED")
        print("="*60)
        print("RIG_A: Silverstone - Time Trial")
        print("RIG_B: Silverstone - Time Trial")
        print("Simulating progressive lap time improvements...")
        print("Press Ctrl+C to stop\n")

        session_uid_a = f"SESSION_{random.randint(10000, 99999)}"
        session_uid_b = f"SESSION_{random.randint(10000, 99999)}"

        lap_num_a = 1
        lap_num_b = 1

        # Simulate different paces for each rig
        # RIG_A will be slightly faster
        rig_a_pace = 0.98  # 2% faster
        rig_b_pace = 1.0

        while True:
            # Send RIG_A data
            rig_a_data = simulate_rig_data('RIG_A', lap_num_a, session_uid_a)
            if lap_num_a > 1:
                rig_a_data['lastLapTimeInMS'] = int(rig_a_data['lastLapTimeInMS'] * rig_a_pace)
            sio.emit('telemetry_update', rig_a_data)

            if lap_num_a > 1:
                lap_time = rig_a_data['lastLapTimeInMS']
                minutes = lap_time // 60000
                seconds = (lap_time % 60000) / 1000
                print(f"[RIG_A] Lap {lap_num_a}: {minutes}:{seconds:06.3f}")

            time.sleep(0.5)

            # Send RIG_B data
            rig_b_data = simulate_rig_data('RIG_B', lap_num_b, session_uid_b)
            if lap_num_b > 1:
                rig_b_data['lastLapTimeInMS'] = int(rig_b_data['lastLapTimeInMS'] * rig_b_pace)
            sio.emit('telemetry_update', rig_b_data)

            if lap_num_b > 1:
                lap_time = rig_b_data['lastLapTimeInMS']
                minutes = lap_time // 60000
                seconds = (lap_time % 60000) / 1000
                print(f"[RIG_B] Lap {lap_num_b}: {minutes}:{seconds:06.3f}")

            time.sleep(0.5)

            # Complete a lap every ~15 seconds (alternating)
            if random.random() > 0.9:
                if random.random() > 0.5:
                    lap_num_a += 1
                else:
                    lap_num_b += 1

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nSimulation stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        sio.disconnect()
        print("Disconnected from gateway")

if __name__ == '__main__':
    run_simulation()
