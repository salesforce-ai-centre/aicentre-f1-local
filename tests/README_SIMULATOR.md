# Dual Rig Telemetry Simulator

This simulator generates fake telemetry data for both RIG_A and RIG_B to test the dual rig dashboard.

## Usage

1. **Start the Flask app** (if not already running):
   ```bash
   python3 src/app.py
   ```

2. **In a separate terminal, run the simulator**:
   ```bash
   python3 tests/dual_rig_simulator.py
   ```

3. **Open the dashboard** in your browser:
   ```
   http://localhost:8080/dual-rig-dashboard
   ```

## What it does

- Simulates telemetry data for both RIG_A and RIG_B
- Generates progressive lap time improvements (laps get faster over time)
- RIG_A is slightly faster than RIG_B (98% vs 100% pace)
- Both rigs simulate Silverstone - Time Trial
- Completes laps randomly every ~15 seconds
- Shows real-time lap times in the terminal

## Testing the Leaderboard

1. Let the simulator run for a few laps on each rig
2. Watch the "Overall Session Best" update in the dashboard
3. Click the **Save icon** (floppy disk) to save the session
4. Enter player names and click Save
5. Toggle between **Combined** and **Split** views
6. Click the **Reset icon** (refresh arrows) to clear current session data
7. Click on any saved lap entry to edit the player name

## Stop the Simulator

Press `Ctrl+C` in the terminal where the simulator is running.
