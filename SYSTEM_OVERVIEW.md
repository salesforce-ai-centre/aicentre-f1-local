# F1 Simulator System - Complete Overview

## 🏎️ What This System Does

This is a **dual F1 simulator racing system** with:
- Real-time telemetry from F1 games
- QR code registration for participants
- Live dashboard showing both racers
- Stream Deck control for race management
- Session tracking and leaderboards

---

## 🖥️ Hardware Setup

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                    F1 SIMULATOR ROOM                            │
│                                                                 │
│  ┌───────────────────┐              ┌───────────────────┐     │
│  │   SIMULATOR 1     │              │   SIMULATOR 2     │     │
│  │   (Left Rig)      │              │   (Right Rig)     │     │
│  │                   │              │                   │     │
│  │ 🖥️  Monitor       │              │ 🖥️  Monitor       │     │
│  │ 🎮  Wheel/Pedals  │              │ 🎮  Wheel/Pedals  │     │
│  │ 💻  PC            │              │ 💻  PC            │     │
│  │     192.168.8.22  │              │     192.168.8.21  │     │
│  │                   │              │                   │     │
│  │ [Attract Screen]  │              │ [Attract Screen]  │     │
│  │  with QR Code     │              │  with QR Code     │     │
│  └───────────────────┘              └───────────────────┘     │
│                                                                 │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │             OVERHEAD DISPLAY (Optional)                 │  │
│  │                                                         │  │
│  │         🖥️  Shows Dual Dashboard                       │  │
│  │             Live telemetry from both rigs              │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│                                                                 │
│  ┌───────────────────┐                                         │
│  │   CONTROL DESK    │                                         │
│  │                   │                                         │
│  │ 💻  MacBook       │                                         │
│  │     (Host PC)     │                                         │
│  │ 172.18.159.209    │                                         │
│  │                   │                                         │
│  │ 🎛️  Stream Deck   │                                         │
│  │   [START]         │                                         │
│  │   [STOP]          │                                         │
│  │   [RESTART]       │                                         │
│  └───────────────────┘                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📱 User Experience Flow

### 1. Participant Arrives
```
User walks up to Simulator 1 or 2
   ↓
Sees attract screen with:
   - QR code
   - Current F1 race info
   - Leaderboards
   ↓
Scans QR code with phone
```

### 2. Registration
```
Phone opens registration form
   ↓
User enters:
   - Nickname
   - Accepts terms & conditions
   - Acknowledges safety rules
   ↓
Submits form
   ↓
Phone shows "Thank You - You're all set!"
   ↓
User puts phone away and sits in simulator
```

### 3. Ready to Race
```
Simulator screen shows:
   "🏁 GAME START! Welcome [NAME]"
   ↓
After 3 seconds, switches to dual dashboard
   ↓
System waits for operator to press START
```

### 4. Race Begins (Operator presses START on Stream Deck)
```
BOTH simulators switch from browser to F1 game
   ↓
Participants start racing
   ↓
Telemetry flows in real-time to dashboard
   ↓
Overhead display shows live data:
   - Speed, RPM, Gear
   - Lap times, sectors
   - Tire temps, fuel
   - Positions, damage
```

### 5. Race Ends (Operator presses STOP on Stream Deck)
```
Sessions marked as "Completed"
   ↓
Results screens show:
   - Best lap time
   - Sector times
   - Top speed
   - Total laps
   ↓
Leaderboards update with new times
```

### 6. Reset (Operator presses RESTART on Stream Deck)
```
All screens return to attract screens
   ↓
System ready for next participants
```

---

## 🔄 Technical Data Flow

```
┌──────────────┐
│  F1 Game     │
│  (Sim 1)     │
│              │
│  UDP Packets │
└──────┬───────┘
       │ Port 20777
       │
       ↓
┌──────────────────────────┐
│  Host PC (MacBook)       │
│  172.18.159.209:8080     │
│                          │
│  ┌────────────────────┐  │
│  │ UDP Receiver #1    │  │
│  │ Port 20777         │  │
│  │ - Decodes packets  │  │
│  │ - Adds rig number  │  │
│  └────────┬───────────┘  │
│           │              │
│           ↓              │
│  ┌────────────────────┐  │
│  │  Flask Server      │  │
│  │  HTTP :8080        │  │
│  │  - Receives data   │  │
│  │  - Broadcasts SSE  │  │
│  │  - Stores sessions │  │
│  └────────┬───────────┘  │
│           │              │
│  ┌────────┴───────────┐  │
│  │  SQLite Database   │  │
│  │  - Sessions        │  │
│  │  - Lap records     │  │
│  │  - Leaderboards    │  │
│  └────────────────────┘  │
└──────────────────────────┘
       │
       │ SSE Stream
       ↓
┌──────────────────┐
│  Web Browsers    │
│  - Attract       │
│  - Dashboard     │
│  - Results       │
└──────────────────┘
```

---

## 📁 File Structure

```
aicentre-f1-local/
├── QUICKSTART.md              ← START HERE!
├── SYSTEM_OVERVIEW.md         ← You are here
├── CLAUDE.md                  ← Full codebase guide
│
├── docs/
│   ├── INSTALLATION.md        ← Complete setup guide
│   ├── STREAM_DECK_CONTROL.md ← Stream Deck configuration
│   └── DEPLOYMENT.md          ← Network details
│
├── scripts/
│   ├── start_mac.sh           ← Start system
│   ├── stop_mac.sh            ← Stop system
│   ├── deploy_to_sim.sh       ← Deploy to Sim 1 or 2
│   ├── control_start_race.sh  ← Stream Deck START
│   ├── control_stop_race.sh   ← Stream Deck STOP
│   └── control_restart.sh     ← Stream Deck RESTART
│
├── src/
│   ├── app.py                 ← Flask server
│   ├── receiver.py            ← UDP telemetry receiver
│   ├── models/                ← Data models
│   ├── repositories/          ← Database access
│   └── services/              ← Business logic
│
├── templates/
│   ├── welcome.html           ← Admin/navigation
│   ├── attract_screen_single.html  ← Sim attract screens
│   ├── start_session.html     ← Registration form
│   ├── thank_you.html         ← Post-registration
│   ├── dual_rig_dashboard.html     ← Live telemetry
│   └── session_summary.html   ← Results screen
│
├── data/
│   └── sessions.db            ← SQLite database
│
└── logs/
    ├── flask.log              ← Web server logs
    ├── receiver-rig1.log      ← Rig 1 telemetry logs
    └── receiver-rig2.log      ← Rig 2 telemetry logs
```

---

## 🎮 Stream Deck Layout

```
┌──────────┬──────────┬──────────┐
│          │          │          │
│  START   │   STOP   │ RESTART  │
│    🏁    │    ⏹️     │    🔄    │
│          │          │          │
│  Green   │   Red    │  Yellow  │
│          │          │          │
└──────────┴──────────┴──────────┘
```

**START** - Switch sims from attract to F1 game  
**STOP** - End race, show results  
**RESTART** - Return to attract screens

---

## 🌐 Network Architecture

```
INTERNET (Mobile Users)
    │
    │ QR Code Scan
    │
    ↓
┌───────────────────────────┐
│  Router                   │
│  Port Forward 80→8080     │
└───────────┬───────────────┘
            │
    ┌───────┴───────┐
    │               │
LOCAL NETWORK     LOCAL NETWORK
192.168.8.x       172.18.x.x
    │               │
┌───┴────┬────┐    │
│        │    │    │
Sim 1   Sim 2 │    Host
.8.22   .8.21 │    .159.209
              │
          (All connected)
```

---

## 🔐 Security & Access

### SSH Credentials
- **Sim 1**: `sim1admin@192.168.8.22` / `Salesforce1`
- **Sim 2**: `sim2admin@192.168.8.21` / `Salesforce1`

### Ports
- **8080** - HTTP (Flask web server)
- **20777** - UDP (Sim 1 telemetry)
- **20778** - UDP (Sim 2 telemetry)

### Internet Access
For mobile QR codes to work from outside the network:
1. Port forward 80→8080 on router
2. Or use Cloudflare Tunnel (recommended)
3. Update QR code URL in attract screens

---

## 📊 Database Schema

```
Session__c
├── Id (UUID)
├── Name (Auto-generated: SES-20231023-RIG1-0001)
├── Driver_Name__c
├── Rig_Number__c (1 or 2)
├── Session_Status__c (Waiting → Active → Completed)
├── Best_Lap_Time__c
├── Best_Sector_1_Time__c
├── Best_Sector_2_Time__c
├── Best_Sector_3_Time__c
├── Top_Speed__c
├── Total_Laps__c
├── Circuit_Name__c
├── Race_Name__c
├── Session_Start_Time__c
├── Session_End_Time__c
└── ... (30+ fields)
```

---

## 🚦 System States

### IDLE / ATTRACT
- Both sims show attract screens with QR codes
- F1 games running in background
- System waiting for participants

### WAITING
- Participant scanned QR code
- Session created but not started
- Driver name visible in system
- Waiting for operator to press START

### ACTIVE
- Operator pressed START
- Both sims showing F1 game
- Telemetry flowing to dashboard
- Race in progress

### COMPLETED
- Operator pressed STOP
- Sessions marked as completed
- Results displayed
- Stats saved to leaderboards

---

## 📈 Features

### Real-Time Telemetry
- Speed (current, average, max)
- RPM, gear, throttle, brake
- Tire temperatures (all 4 corners)
- Tire wear percentage
- Fuel level and consumption
- Lap times and sectors
- Position and gaps
- DRS status
- ERS modes
- Damage indicators

### Session Management
- QR code registration
- Driver name tracking
- Best lap detection
- Sector time tracking
- Session duration
- Automatic leaderboards

### Leaderboards
- Daily best times
- Monthly best times
- Track-specific records
- Multi-rig support

### Control System
- Stream Deck integration
- Window switching via SSH
- Automatic state management
- Race start/stop/restart

---

## 🎯 Quick Command Reference

### Start System
```bash
./scripts/start_mac.sh
```

### Stop System
```bash
./scripts/stop_mac.sh
```

### Deploy to Sims
```bash
./scripts/deploy_to_sim.sh 1  # Sim 1
./scripts/deploy_to_sim.sh 2  # Sim 2
```

### Control Race
```bash
curl -X POST http://localhost:8080/api/control/start-race
curl -X POST http://localhost:8080/api/control/stop-race
curl -X POST http://localhost:8080/api/control/restart
```

### View Logs
```bash
tail -f logs/*.log
```

---

## 📚 Documentation Map

1. **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 steps
2. **[INSTALLATION.md](docs/INSTALLATION.md)** - Detailed setup for all 3 PCs
3. **[STREAM_DECK_CONTROL.md](docs/STREAM_DECK_CONTROL.md)** - Stream Deck configuration
4. **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Network and production setup
5. **[CLAUDE.md](CLAUDE.md)** - Technical architecture and code guide

---

## 🆘 Support

**Check logs first:**
```bash
tail -f logs/*.log
```

**Test network:**
```bash
ping 192.168.8.22  # Sim 1
ping 192.168.8.21  # Sim 2
```

**Verify services:**
```bash
ps aux | grep python
lsof -i :8080
```

**Reset everything:**
```bash
./scripts/stop_mac.sh
./scripts/start_mac.sh
```

---

**Ready to race? Start with [QUICKSTART.md](QUICKSTART.md)! 🏁**
