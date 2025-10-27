# Stream Deck Control System

## Overview

This system allows you to control the F1 simulator setup via Stream Deck buttons. Three main buttons control the entire flow.

## System Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    IDLE / ATTRACT STATE                      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Sim 1      │  │   Sim 2      │  │   Host       │      │
│  │   Browser    │  │   Browser    │  │   Browser    │      │
│  │              │  │              │  │              │      │
│  │   Attract    │  │   Attract    │  │   Attract    │      │
│  │   Screen     │  │   Screen     │  │   Screen     │      │
│  │   (QR Code)  │  │   (QR Code)  │  │  (Overview)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  F1 Game running in background on each sim                  │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ User scans QR code, enters name
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              SESSION CREATED (Waiting State)                 │
│                                                              │
│  Driver names appear in system, ready to start              │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ Press START button on Stream Deck
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                      RACE IN PROGRESS                        │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Sim 1      │  │   Sim 2      │  │   Host       │      │
│  │              │  │              │  │              │      │
│  │   F1 GAME    │  │   F1 GAME    │  │    DUAL      │      │
│  │   (Active)   │  │   (Active)   │  │  DASHBOARD   │      │
│  │              │  │              │  │  (Live Data) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  Telemetry flowing from both games to dashboard             │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ Press STOP button on Stream Deck
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                      RESULTS SCREEN                          │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Sim 1      │  │   Sim 2      │  │   Host       │      │
│  │   Browser    │  │   Browser    │  │   Browser    │      │
│  │              │  │              │  │              │      │
│  │   Results    │  │   Results    │  │   Results    │      │
│  │   Summary    │  │   Summary    │  │   Summary    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  Sessions marked as "Completed", stats displayed            │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ Press RESTART button on Stream Deck
                           ↓
                    (Back to IDLE / ATTRACT STATE)
```

## Stream Deck Buttons

### 1. START Button (Green)
**Function**: Begins the race

**What it does:**
1. Switches Sim 1 from Chrome (attract screen) to F1 game window
2. Switches Sim 2 from Chrome (attract screen) to F1 game window
3. Switches Host to dual dashboard
4. Sessions remain in "Active" state
5. Telemetry starts flowing to dashboard

**Script**: `./scripts/control_start_race.sh`

**API**: `POST /api/control/start-race`

**Stream Deck Setup**:
- Action: System → Website
- URL: `http://172.18.159.209:8080/api/control/start-race`
- Method: POST

---

### 2. STOP Button (Red)
**Function**: Ends the race and shows results

**What it does:**
1. Marks both active sessions as "Completed"
2. Calculates final stats (best lap, sectors, etc.)
3. Both sims stay on F1 game (or you manually bring up browser)
4. Host shows combined results screen
5. After 10 seconds, ready for RESTART

**Script**: `./scripts/control_stop_race.sh`

**API**: `POST /api/control/stop-race`

**Stream Deck Setup**:
- Action: System → Website
- URL: `http://172.18.159.209:8080/api/control/stop-race`
- Method: POST

---

### 3. RESTART Button (Yellow)
**Function**: Resets everything to attract screens

**What it does:**
1. Completes any lingering active sessions
2. Switches Sim 1 browser back to attract screen (refreshes page)
3. Switches Sim 2 browser back to attract screen (refreshes page)
4. Switches Host browser to host attract screen
5. System ready for next participants

**Script**: `./scripts/control_restart.sh`

**API**: `POST /api/control/restart`

**Stream Deck Setup**:
- Action: System → Website
- URL: `http://172.18.159.209:8080/api/control/restart`
- Method: POST

---

## Prerequisites

### On Both Sim PCs (192.168.8.22 & 192.168.8.21)

1. **Install window management tools**:
   ```bash
   sudo apt install wmctrl xdotool
   ```

2. **F1 Game Setup**:
   - Game should be running in the background
   - Can be minimized but not closed
   - Telemetry enabled (UDP to 172.18.159.209:20777/20778)

3. **Browser Setup**:
   - Chrome in kiosk mode
   - Auto-loads attract screen on startup
   - Should be the active window initially

4. **SSH Access**:
   - Passwordless SSH from host (run setup_ssh_keys.sh)
   - Or use sshpass if passwords required

### On Host PC (Your MacBook - 172.18.159.209)

1. **System Running**:
   ```bash
   ./scripts/start_mac.sh
   ```

2. **Stream Deck Software Installed**

3. **Network Access**:
   - Can SSH to both sim PCs
   - Flask server running on port 8080

---

## Stream Deck Configuration

### Button 1: START RACE

**Title**: START 🏁
**Style**: Green background
**Action**: System → Open
**Path**: `/Users/jacob.berry/Developer/aicentre-f1-local/scripts/control_start_race.sh`

Alternative (HTTP method):
**Action**: Website
**URL**: `http://localhost:8080/api/control/start-race`
**Access Page On**: Key Press
**HTTP Method**: POST

---

### Button 2: STOP RACE

**Title**: STOP ⏹️
**Style**: Red background
**Action**: System → Open
**Path**: `/Users/jacob.berry/Developer/aicentre-f1-local/scripts/control_stop_race.sh`

Alternative (HTTP method):
**Action**: Website
**URL**: `http://localhost:8080/api/control/stop-race`
**Access Page On**: Key Press
**HTTP Method**: POST

---

### Button 3: RESTART

**Title**: RESTART 🔄
**Style**: Yellow background
**Action**: System → Open
**Path**: `/Users/jacob.berry/Developer/aicentre-f1-local/scripts/control_restart.sh`

Alternative (HTTP method):
**Action**: Website
**URL**: `http://localhost:8080/api/control/restart`
**Access Page On**: Key Press
**HTTP Method**: POST

---

## Testing the Control System

### Manual Testing (Without Stream Deck)

```bash
# Test START
curl -X POST http://localhost:8080/api/control/start-race

# Test STOP
curl -X POST http://localhost:8080/api/control/stop-race

# Test RESTART
curl -X POST http://localhost:8080/api/control/restart
```

### Full Integration Test

1. **Initial State**:
   - All 3 screens showing attract screens
   - F1 games running in background on both sims

2. **Create Sessions**:
   - Scan QR code on Sim 1 with phone
   - Enter name "Driver 1", accept terms
   - Scan QR code on Sim 2 with phone
   - Enter name "Driver 2", accept terms

3. **Start Race**:
   - Press START button on Stream Deck
   - Verify: Both sims switch to F1 game window
   - Verify: Host shows dual dashboard with both driver names

4. **Stop Race**:
   - Press STOP button on Stream Deck
   - Verify: Sessions marked as completed
   - Verify: Results displayed

5. **Restart**:
   - Press RESTART button on Stream Deck
   - Verify: All screens return to attract screens
   - Verify: Ready for next race

---

## Troubleshooting

### START button doesn't switch windows

**Problem**: Sims stay on attract screen

**Solutions**:
1. Check SSH access: `ssh sim1admin@192.168.8.22 "echo test"`
2. Verify wmctrl is installed: `ssh sim1admin@192.168.8.22 "which wmctrl"`
3. Check F1 game is running: `ssh sim1admin@192.168.8.22 "ps aux | grep F1"`
4. Try manual command: `ssh sim1admin@192.168.8.22 "DISPLAY=:0 wmctrl -l"`

### STOP button doesn't complete sessions

**Problem**: Sessions stay in "Active" state

**Solutions**:
1. Check Flask logs: `tail -f logs/flask.log`
2. Verify sessions exist: `curl http://localhost:8080/api/session/active/1`
3. Manually complete: `./scripts/reset_session.sh`

### RESTART button doesn't refresh browsers

**Problem**: Browsers don't return to attract screen

**Solutions**:
1. Check SSH connection to sims
2. Verify Chrome is running: `ssh sim1admin@192.168.8.22 "ps aux | grep chrome"`
3. Try manual refresh: `ssh sim1admin@192.168.8.22 "DISPLAY=:0 xdotool key F5"`

---

## Advanced: Window Switching Commands

### List all windows on a sim:
```bash
ssh sim1admin@192.168.8.22 "DISPLAY=:0 wmctrl -l"
```

### Switch to specific window by name:
```bash
ssh sim1admin@192.168.8.22 "DISPLAY=:0 wmctrl -a 'F1 25'"
```

### Get active window:
```bash
ssh sim1admin@192.168.8.22 "DISPLAY=:0 xdotool getactivewindow getwindowname"
```

### Simulate key press:
```bash
ssh sim1admin@192.168.8.22 "DISPLAY=:0 xdotool key Alt+Tab"
```

---

## API Reference

### Control Endpoints

```bash
# Start race (switch to game)
POST /api/control/start-race
Response: {"success": true, "message": "Race started - sims switching to game window"}

# Stop race (show results)
POST /api/control/stop-race
Response: {"success": true, "message": "Race stopped", "completedRigs": [1, 2]}

# Restart (back to attract)
POST /api/control/restart
Response: {"success": true, "message": "System restarted - back to attract screens"}
```

### Session Management

```bash
# Get active session for rig
GET /api/session/active/{rigNumber}

# Complete specific session
POST /api/session/{sessionId}/complete

# Get leaderboards
GET /api/leaderboard/daily
GET /api/leaderboard/monthly
GET /api/leaderboard/track?track=Silverstone
```

---

## Host Attract Screen

The host also needs its own attract screen showing:
- Current race from calendar
- Next 3 upcoming races
- Combined leaderboards (both rigs)
- System status

TODO: Create `templates/attract_screen_host.html`

