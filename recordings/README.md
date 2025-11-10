# F1 UDP Packet Recording & Playback

This directory contains tools and recorded UDP packet data for debugging and testing the F1 telemetry system.

## Quick Start

### Recording Packets

#### Recording from Multiple Rigs Simultaneously (Recommended for Spectator PC)

If you're running on the receiver PC with spectator view, record from all rigs at once:

```bash
# Record from both RIG A (20777) and RIG B (20778) simultaneously
python3 scripts/record_all_rigs.py recordings/lan_session

# Record from custom ports
python3 scripts/record_all_rigs.py recordings/custom_session 20777 20778 20779

# Creates separate files for each port:
#   recordings/lan_session/rig_port20777_20231110_143022.packets
#   recordings/lan_session/rig_port20778_20231110_143022.packets
```

**Features:**
- Records all ports simultaneously in separate files
- Real-time statistics showing packets/sec for each port
- Automatic timestamped filenames
- Press Ctrl+C to stop all recordings at once

#### Recording Individual Rigs

Record UDP packets from a single port:

```bash
# Record from RIG_A (port 20777) for 60 seconds
python3 scripts/record_udp_packets.py --port 20777 --output recordings/rig_a_lan_game.packets --duration 60

# Record from RIG_B (port 20778) for 120 seconds
python3 scripts/record_udp_packets.py --port 20778 --output recordings/rig_b_lan_game.packets --duration 120

# Record unlimited duration (press Ctrl+C to stop)
python3 scripts/record_udp_packets.py --port 20777 --output recordings/rig_a_unlimited.packets --duration 0
```

### Analyzing Recordings

Inspect the contents of a recording:

```bash
# Basic analysis
python3 scripts/analyze_udp_packets.py --input recordings/rig_a_lan_game.packets

# Detailed analysis with sample data
python3 scripts/analyze_udp_packets.py --input recordings/rig_a_lan_game.packets --details
```

This will show you:
- Total packets recorded
- Packet type breakdown (Motion, Lap Data, Telemetry, etc.)
- Player indices seen in the recording
- Session UIDs
- Lap data statistics (positions, lap times, etc.)

### Playing Back Recordings

Replay recorded packets to test the dashboard:

```bash
# Playback at normal speed to port 20777
python3 scripts/playback_udp_packets.py --input recordings/rig_a_lan_game.packets --port 20777

# Playback at 2x speed
python3 scripts/playback_udp_packets.py --input recordings/rig_a_lan_game.packets --port 20777 --speed 2.0

# Loop playback indefinitely
python3 scripts/playback_udp_packets.py --input recordings/rig_a_lan_game.packets --port 20777 --loop

# Send to remote host
python3 scripts/playback_udp_packets.py --input recordings/rig_a_lan_game.packets --host 192.168.1.100 --port 20777
```

## Debugging LAN Game Issues

To debug the multiplayer/LAN game issues with lap times and positions:

### Step 1: Record from Both Rigs

```bash
# Terminal 1 - Record RIG_A
python3 scripts/record_udp_packets.py --port 20777 --output recordings/rig_a_lan_session.packets --duration 120

# Terminal 2 - Record RIG_B
python3 scripts/record_udp_packets.py --port 20778 --output recordings/rig_b_lan_session.packets --duration 120
```

### Step 2: Analyze Both Recordings

```bash
# Analyze RIG_A recording
python3 scripts/analyze_udp_packets.py --input recordings/rig_a_lan_session.packets --details > rig_a_analysis.txt

# Analyze RIG_B recording
python3 scripts/analyze_udp_packets.py --input recordings/rig_b_lan_session.packets --details > rig_b_analysis.txt
```

Look for:
- Are both rigs seeing the same `player_index`? (They should be different!)
- Are positions updating? (Should see multiple positions in "Positions seen")
- Are lap times being recorded? (Should see non-zero lap times)
- Is the result_status `2` (active)? (Not `0` or `1` which means inactive)

### Step 3: Test with Playback

Stop your game and test the dashboard with recorded data:

```bash
# Start dashboard (in one terminal)
python3 scripts/run_dual_dashboard.py

# Playback RIG_A data (in another terminal)
python3 scripts/playback_udp_packets.py --input recordings/rig_a_lan_session.packets --port 20777

# Playback RIG_B data (in a third terminal)
python3 scripts/playback_udp_packets.py --input recordings/rig_b_lan_session.packets --port 20778
```

Watch the dashboard and check if:
- Position updates correctly
- Lap times appear
- Car moves on track map

## File Format

Recorded packet files use a custom binary format:

```
[Metadata Size: 4 bytes]
[Metadata JSON: variable length]
[Separator: "---PACKETS---\n"]
[Packet 1: timestamp (8 bytes) + size (4 bytes) + data (variable)]
[Packet 2: timestamp (8 bytes) + size (4 bytes) + data (variable)]
...
```

Metadata includes:
- `recording_start`: ISO timestamp when recording started
- `recording_end`: ISO timestamp when recording ended
- `port`: UDP port that was recorded
- `packet_count`: Total number of packets
- `duration`: Recording duration in seconds

## Tips

1. **Record at least 2-3 laps** to capture lap completion events
2. **Include practice/qualifying and race** scenarios to test different modes
3. **Keep recordings under 5 minutes** to keep file sizes manageable
4. **Name recordings descriptively**: e.g., `rig_a_silverstone_race_p1.packets`
5. **Use --details flag** when analyzing to see actual lap data values

## Troubleshooting

**No packets recorded:**
- Check F1 game UDP settings (Port, Broadcast mode)
- Verify firewall isn't blocking UDP
- Try running as administrator/sudo

**Playback not working:**
- Ensure target port is available (not in use by game)
- Check dashboard is listening on the correct port
- Try with --speed 1.0 first before adjusting

**Analysis shows all zeros:**
- Recording might be too short (try 60+ seconds)
- Game might not be sending data (check game settings)
- Port mismatch between game and recorder

## Example Scenarios

### Scenario 1: Debug Time Trial (Single Player)
```bash
# Record
python3 scripts/record_udp_packets.py --port 20777 --output recordings/time_trial_silverstone.packets --duration 180

# Analyze
python3 scripts/analyze_udp_packets.py --input recordings/time_trial_silverstone.packets --details

# Expected: player_index=0, position=1, lap times recorded
```

### Scenario 2: Debug LAN Game (Multiplayer)
```bash
# Record both rigs simultaneously during LAN game
python3 scripts/record_udp_packets.py --port 20777 --output recordings/lan_rig_a.packets --duration 180 &
python3 scripts/record_udp_packets.py --port 20778 --output recordings/lan_rig_b.packets --duration 180 &

# Wait for recordings to complete, then analyze
python3 scripts/analyze_udp_packets.py --input recordings/lan_rig_a.packets --details
python3 scripts/analyze_udp_packets.py --input recordings/lan_rig_b.packets --details

# Compare player_index values - they should be different!
```

## Web-Based Packet Playback

You can now analyze and play back recordings directly in the dual-rig dashboard:

### Access the Playback Page

```bash
# Start the dashboard
python3 scripts/run_dual_dashboard.py

# Open your browser to:
http://localhost:8080/playback
```

### Features

- **Drag & Drop**: Upload `.packets` files directly in the browser
- **Playback Controls**: Play, pause, stop with speed control (0.25x to 5x)
- **Target Port Selection**: Choose which rig to send to (20777 for RIG_A, 20778 for RIG_B)
- **Loop Mode**: Continuously replay for extended testing
- **Metadata Display**: View recording info (duration, packet count, date, port)
- **Progress Tracking**: Real-time progress bar and packet counter

### Typical Workflow

1. Record packets from both rigs during a LAN session
2. Open the playback page at `http://localhost:8080/playback`
3. Upload RIG_A recording and play it back to port 20777
4. Open a second browser tab for RIG_B recording to port 20778
5. Watch the main dashboard to verify both rigs display correctly
6. Adjust playback speed or loop to test different scenarios

**Note**: The web playback UI is currently frontend-only. For full playback functionality with actual UDP transmission, use the command-line `playback_udp_packets.py` script.

## Next Steps

After recording and analyzing, share the analysis output to diagnose:
- Which player index each rig is using
- Whether lap data is being populated
- If positions are updating
- If both rigs are receiving the same or different UDP streams
