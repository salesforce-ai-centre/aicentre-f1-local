# F1 25 Telemetry Updates

## Overview

The F1 telemetry dashboard has been updated to support both F1 25 and F1 24 games. The system automatically detects the game version based on the packet format and handles the differences appropriately.

## Key Changes for F1 25 Support

### 1. Packet Format Detection
- **F1 25**: `m_packetFormat` = 2025
- **F1 24**: `m_packetFormat` = 2024
- The receiver automatically handles both formats

### 2. New Features in F1 25

#### A. Tyre Blisters Data
- Added `m_tyreBlisters` field to `CarDamageData` structure
- Array of 4 values (one per tyre: RL, RR, FL, FR) showing blister percentage
- Automatically defaults to `[0, 0, 0, 0]` for F1 24 compatibility

#### B. New C6 Tyre Compound
- Added support for C6 compound (ID: 22)
- The softest compound in the F1 tyre range
- Tyre compound mapping: C0 (hardest) → C6 (softest)

#### C. Lap Positions Packet (ID: 15)
- New packet type for tracking car positions throughout the race
- Contains position history for all cars at the start of each lap
- Can be used to generate position charts over the race duration
- Only available in F1 25 (ignored for F1 24)
- Stores up to 50 laps of position data per packet

#### D. Motion Ex Updates (Planned)
- Chassis pitch angle data
- Wheel camber and camber gain arrays
- (Note: Full Motion Ex packet support to be added in future updates)

### 3. Backwards Compatibility
- The system maintains full compatibility with F1 24
- Automatically detects game version and adjusts packet parsing
- F1 24 clients continue to work without any changes

## Configuration

### Game Settings

#### For F1 25:
1. Go to Settings → Telemetry Settings
2. Set UDP Telemetry: ON
3. Set UDP Port: 20777 (default)
4. Set UDP Format: **F1 2025**
5. Configure UDP Broadcast Mode for your network

#### For F1 24:
1. Go to Settings → Telemetry Settings
2. Set UDP Telemetry: ON
3. Set UDP Port: 20777 (default)
4. Set UDP Format: **F1 2024**
5. Configure UDP Broadcast Mode for your network

## Usage

The system works exactly the same as before:

```bash
# Start the dashboard
python3 scripts/run_dashboard.py --driver "Your Name" --datacloud

# Or start components separately
python3 src/app.py                    # Flask server
python3 src/receiver.py --url http://localhost:8080/data --driver "Your Name"
```

## Technical Details

### Updated Files
- **src/receiver.py**: Main changes for F1 25 packet support
  - Updated packet format checking to accept both 2024 and 2025
  - Added CarDamageData structure updates for tyre blisters
  - Added PacketLapPositions handling
  - Added C6 tyre compound to mapping

- **CLAUDE.md**: Documentation updates
  - Updated references from F1 24 to F1 25/24
  - Added new F1 25 documentation references
  - Updated configuration instructions

### Data Structure Changes

#### CarDamageData (F1 25)
```python
# F1 25 adds tyre blisters after brakes damage
m_tyreBlisters: List[int]  # [RL, RR, FL, FR] percentages
```

#### PacketLapPositions (F1 25 Only)
```python
m_numLaps: int              # Number of laps in the data
m_lapStart: int             # Starting lap index
m_positionForVehicleIdx: List[List[int]]  # Position data
```

## Testing Status

- [x] Packet format detection for F1 25/24
- [x] C6 tyre compound support
- [x] CarDamageData with tyre blisters
- [x] PacketLapPositions packet handling
- [x] Documentation updates
- [ ] Live testing with F1 25 game (pending)

## Known Limitations

1. Motion Ex packet enhancements (chassis pitch, wheel camber) not fully implemented yet
2. Event packet stop-go penalty time field not yet integrated into event handling
3. Participant data livery colors not displayed in UI (backend support ready)

## Future Enhancements

1. Complete Motion Ex packet support with new F1 25 fields
2. UI updates to display tyre blister information
3. Position chart visualization using lap positions data
4. Display car livery colors in participant list

## Troubleshooting

If you encounter issues:

1. **Check packet format**: Ensure your game is set to the correct UDP format (F1 2025 for F1 25, F1 2024 for F1 24)
2. **Port conflicts**: Make sure port 20777 is not in use
3. **Version mismatch warnings**: If you see "Ignoring packet with format..." warnings, verify your game settings
4. **Missing data**: Some F1 25 features (like lap positions) won't appear when using F1 24

## Support

For issues or questions about F1 25 support, please check:
- The main README.md for general setup
- CLAUDE.md for detailed technical documentation
- Create an issue on GitHub if you encounter bugs