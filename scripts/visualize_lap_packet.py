#!/usr/bin/env python3
"""
Visualize Lap Data packets in a readable format
Usage: Pass packet data via stdin or as argument
"""

import sys
import re

def extract_result_status(status):
    statuses = {
        0: "INACTIVE",
        1: "DNF",
        2: "ACTIVE",
        3: "FINISHED",
        4: "DSQ",
        5: "NOT_CLASSIFIED",
        6: "RETIRED"
    }
    return statuses.get(status, f"UNKNOWN({status})")

def extract_driver_status(status):
    statuses = {
        0: "IN_GARAGE",
        1: "FLYING_LAP",
        2: "IN_LAP",
        3: "OUT_LAP",
        4: "ON_TRACK"
    }
    return statuses.get(status, f"UNKNOWN({status})")

def visualize_lap_packet(packet_str):
    """Visualize a lap data packet"""

    # Extract header info
    header_match = re.search(r'm_playerCarIndex=(\d+)', packet_str)
    session_time_match = re.search(r'm_sessionTime=([\d.]+)', packet_str)

    if header_match:
        player_car_index = int(header_match.group(1))
        session_time = float(session_time_match.group(1)) if session_time_match else 0

        print("=" * 100)
        print(f"📊 LAP DATA PACKET VISUALIZATION")
        print("=" * 100)
        print(f"🎮 Header says player is at index: {player_car_index}")
        print(f"⏱️  Session Time: {session_time:.2f}s")
        print("=" * 100)
        print()

    # Find all LapData entries
    lap_data_pattern = r'LapData\(([^)]+(?:\([^)]*\))?[^)]*)\)'
    lap_datas = re.finditer(lap_data_pattern, packet_str)

    active_cars = []

    for car_idx, match in enumerate(lap_datas):
        lap_data_str = match.group(1)

        # Extract key fields
        fields = {}
        for field in ['m_lastLapTimeInMS', 'm_currentLapTimeInMS', 'm_lapDistance',
                      'm_carPosition', 'm_currentLapNum', 'm_driverStatus', 'm_resultStatus']:
            field_match = re.search(f'{field}=([^,]+)', lap_data_str)
            if field_match:
                value_str = field_match.group(1)
                try:
                    if 'MS' in field or 'Num' in field or 'Status' in field or 'Position' in field:
                        fields[field] = int(value_str)
                    else:
                        fields[field] = float(value_str)
                except:
                    fields[field] = 0

        # Check if car has data
        has_data = (
            fields.get('m_currentLapNum', 0) > 0 or
            fields.get('m_carPosition', 0) > 0 or
            abs(fields.get('m_lapDistance', 0)) > 0.1
        )

        if has_data:
            active_cars.append((car_idx, fields))

    # Display active cars
    if active_cars:
        print(f"✅ ACTIVE CARS ({len(active_cars)} found):\n")

        for car_idx, fields in active_cars:
            is_player = "🎮 PLAYER" if car_idx == player_car_index else ""
            warning = ""

            # Check for invalid data
            if fields.get('m_resultStatus') != 2:  # Not ACTIVE
                warning = f" ⚠️  resultStatus={extract_result_status(fields.get('m_resultStatus', 0))}"

            if abs(fields.get('m_lapDistance', 0)) > 1e10:
                warning += " 🔴 CORRUPTED DATA"

            print(f"  Car #{car_idx:2d} {is_player:15s} {warning}")
            print(f"    Position:        {fields.get('m_carPosition', 0)}")
            print(f"    Lap:             {fields.get('m_currentLapNum', 0)}")
            print(f"    Lap Distance:    {fields.get('m_lapDistance', 0):.2f}m")
            print(f"    Current Lap Time: {fields.get('m_currentLapTimeInMS', 0)}ms")
            print(f"    Last Lap Time:   {fields.get('m_lastLapTimeInMS', 0)}ms")
            print(f"    Driver Status:   {extract_driver_status(fields.get('m_driverStatus', 0))}")
            print(f"    Result Status:   {extract_result_status(fields.get('m_resultStatus', 0))}")
            print()
    else:
        print("❌ No active cars found in packet\n")

    # Display the bug
    if header_match:
        player_has_data = any(car_idx == player_car_index for car_idx, _ in active_cars)

        print("=" * 100)
        print("🔍 ANALYSIS:")
        print("=" * 100)

        if player_has_data:
            print(f"✅ Header player_index ({player_car_index}) HAS DATA - This is correct!")
        else:
            print(f"❌ Header player_index ({player_car_index}) HAS NO DATA - This is the BUG!")
            if active_cars:
                actual_player_indices = [idx for idx, _ in active_cars]
                print(f"💡 Active cars are at indices: {actual_player_indices}")
                print(f"🔧 Auto-detection should use index {actual_player_indices[0]} instead")

        print("=" * 100)

def main():
    if len(sys.argv) > 1:
        packet_str = ' '.join(sys.argv[1:])
    else:
        packet_str = sys.stdin.read()

    visualize_lap_packet(packet_str)

if __name__ == "__main__":
    main()
