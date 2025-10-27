# F1 25 Telemetry Application - Feature Analysis

**Date:** 2025-10-21
**Source:** `/Users/jacob.berry/Developer/aicentre-f1-local/f1-25-telemetry-application-main`
**Analysis for:** Dual-Rig F1 Telemetry Dashboard Enhancement

---

## Executive Summary

This document analyzes a sophisticated F1 telemetry desktop application built with PySide6 (Qt framework) to identify features that could enhance our Flask/WebSocket-based dual-rig dashboard. The reference application is a production-grade, multi-tabbed desktop app supporting F1 25, 24, 23, and 22 game versions with advanced visualization capabilities.

**Key Differentiator:** Desktop app (Qt/PySide6) vs our web-based app (Flask/WebSocket/JavaScript)

---

## 🎯 High-Value Features to Add

### **1. Multi-Driver Comparison Tables** ⭐⭐⭐
The reference app has sophisticated multi-driver tables across 9 tabs. For our dual-rig setup:

**Features:**
- **Lap Times Table**: Compare last lap, best lap, and sector times (S1/S2/S3) between drivers
- **Damage Comparison**: Side-by-side component damage monitoring (front wing, rear wing, floor, diffuser, sidepod)
- **Temperature Monitoring**: Inner vs outer tyre temps for both drivers in a comparison view
- **Tyre Wear Per Lap Calculation**: Shows predicted remaining tyre life based on current wear rate

**Implementation Value:** HIGH - Easy to add to our existing table structure

---

### **2. Track Map Visualization** ⭐⭐⭐

**Features:**
- **2D track rendering** with real racing lines from 32+ circuits
- **Marshal zone visualization** color-coded by flag status (yellow/green/red)
- **Live car position markers** on the track
- **Auto-track detection** from session packets
- **Dynamic scaling** to fit any track layout

**For Dual-Rig:**
- Show both drivers' positions on the same track in real-time
- Visual comparison of lap progress
- Distance between drivers displayed spatially

**Technical Implementation:**
- Track data stored in CSV files (distance, x, y, z coordinates)
- Canvas rendering using HTML5 Canvas or SVG
- Real-time position updates from motion packets

**Implementation Value:** VERY HIGH - Most impressive visual upgrade

---

### **3. Race Director Event Log** ⭐⭐⭐

**Events Tracked:**
- Fastest lap announcements
- DRS enabled/disabled notifications
- Retirement events (with reasons: mechanical failure, damage, disqualification, etc.)
- Lights out / formation lap tracking
- Session flag changes (yellow, red, green)
- Speed trap achievements
- Penalty notifications

**Implementation:** Chronological feed (newest at top) with emoji indicators

**Implementation Value:** HIGH - Helps track key moments without watching raw numbers

---

### **4. Speed Trap Analytics** ⭐⭐

**Features:**
- Tracks fastest speed through speed trap zones
- Shows position ranking in speed trap
- Session-wide leaderboard
- Useful for comparing straight-line speed between drivers

**For Dual-Rig:**
- Direct comparison metric between two drivers
- Identifies aero setup differences
- DRS analysis

**Implementation Value:** MEDIUM - Nice comparison metric

---

### **5. Weather Forecast Display** ⭐⭐

**Features:**
- Multi-session weather lookahead
- Temperature trends with visual indicators (🔼 rising, 🔽 falling, ▶️ stable)
- Rain percentage forecasting
- 6 weather types: ☀️ Clear, 🌥️ Light Cloud, ☁️ Overcast, 🌦️ Light Rain, 🌧️ Heavy Rain, ⛈️ Storm

**Data:**
- Air temperature
- Track temperature
- Weather accuracy indicator (Perfect/Approximative)
- Time offset for each forecast sample

**Implementation Value:** MEDIUM - Useful for strategy planning in longer races

---

### **6. Sector Time Analysis** ⭐⭐

**Features:**
- Current lap: S1 / S2 / S3 times
- Best lap sectors
- Last lap sectors
- Sector-by-sector comparison

**For Dual-Rig:**
- Easy to spot where one driver is faster than the other
- Identify weak/strong corners
- Compare sector consistency

**Implementation Value:** HIGH - Easy to implement, high value for comparing drivers

---

### **7. ERS/Fuel Management Display** ⭐⭐

**Features:**
- Color-coded ERS percentage (red→yellow→green interpolation)
- ERS mode display:
  - NONE
  - MEDIUM
  - HOTLAP
  - OVERTAKE
- Fuel remaining in laps (not just raw kg)
- Fuel mix mode:
  - Lean
  - Standard
  - Rich
  - Max

**Implementation Value:** MEDIUM - More detailed power unit monitoring

---

### **8. Network Diagnostics Tab** ⭐

**Features:**
- Packet reception rate monitoring (packets/second)
- 16 packet types tracked:
  - Motion (0), Session (1), Lap Data (2), Event (3)
  - Participants (4), Car Setup (5), Telemetry (6), Car Status (7)
  - Car Damage (10), Motion Ex (13), and more
- Performance diagnostics for network stability

**For Dual-Rig:**
- CRUCIAL - Shows if one rig has connection problems
- Identifies packet loss
- Validates protocol compliance

**Implementation Value:** HIGH - Critical for debugging dual-rig issues

---

### **9. Tyre Compound & Age Display** ⭐

**Features:**
- Visual compound indicator (Soft/Medium/Hard/Intermediate/Wet)
- Tyre age in laps
- Color coding: 🔴 Soft, 🟡 Medium, ⚪ Hard, 🟢 Intermediate, 🔵 Wet
- Quad layout showing all 4 tyres:
  ```
  [FL] [FR]
  [RL] [RR]
  ```

**Implementation Value:** MEDIUM - Currently missing from our dashboard

---

### **10. Gap to Leader / Gap to Car Ahead** ⭐

**Features:**
- Real-time gap calculations
- Time delta in seconds with millisecond precision
- Gap to car ahead
- Gap to race leader

**For Dual-Rig:**
- Show gap between the two drivers
- Track who's pulling away or catching up

**Implementation Value:** MEDIUM - Good performance metric

---

## 🏗️ Architectural Improvements

### **Multi-Tab Organization**

Instead of cramming everything into one scrolling page, organize by category:

```
├── Overview Tab      → Speed, gear, RPM, position, lap times
├── Tyres Tab        → Temps, wear, compound, age
├── Damage Tab       → All component damage
├── Power Tab        → ERS, fuel, DRS
├── Map Tab          → Track visualization
├── Events Tab       → Race director log
├── Diagnostics Tab  → Network health (packet rates)
```

**Implementation:** Use CSS tabs or Bootstrap tabs in web dashboard

---

### **Custom Rendering for Tyre Data**

The reference app uses a "quad delegate" that renders 4 values in a 2×2 grid within a single table cell.

**Example Display:**
```
Tyre Temps:
┌─────┬─────┐
│ 95° │ 94° │  FL  FR
├─────┼─────┤
│ 98° │ 97° │  RL  RR
└─────┴─────┘
```

**Implementation:** CSS Grid layout within table cells

---

### **Color Interpolation System**

Dynamic color coding based on values:

- **ERS**:
  - 0% = `#e74c3c` (red)
  - 50% = `#90ee90` (light green)
  - 100% = `#2ecc71` (dark green)

- **Damage**:
  - 0% = `#2ecc71` (green)
  - 50% = `#f39c12` (yellow)
  - 100% = `#e74c3c` (red)

- **Tyre Temp**:
  - Cold (<80°C) = `#3498db` (blue)
  - Optimal (80-105°C) = `#2ecc71` (green)
  - Hot (>105°C) = `#e74c3c` (red)

**Implementation:** JavaScript color interpolation functions

---

### **Player State Object**

Instead of passing raw packet data, create a comprehensive `Player` object per rig:

```javascript
class Player {
  // Position & Lap Data
  position: int
  currentLap: int
  lapDistance: float
  lastLapTime: int
  bestLapTime: int
  currentLapTime: int

  // Sector Times
  currentSectors: [s1, s2, s3]
  lastLapSectors: [s1, s2, s3]
  bestLapSectors: [s1, s2, s3]

  // Tyre Management
  tyreCompound: string  // "S", "M", "H", "I", "W"
  tyresAgeLaps: int
  tyreWear: [FL, FR, RL, RR]
  tyreTempInner: [FL, FR, RL, RR]
  tyreTempSurface: [FL, FR, RL, RR]

  // Power & Fuel
  ersPourcentage: float
  ersMode: int  // 0=None, 1=Medium, 2=Hotlap, 3=Overtake
  fuelRemainingLaps: float
  fuelMix: int  // 0=Lean, 1=Standard, 2=Rich, 3=Max

  // DRS
  drsAllowed: bool
  drsActive: bool
  drsActivationDistance: int

  // Damage
  frontLeftWingDamage: float
  frontRightWingDamage: float
  rearWingDamage: float
  floorDamage: float
  diffuserDamage: float
  sidepodDamage: float

  // Speed & Telemetry
  speed: int
  speedTrapSpeed: int
  speedTrapPosition: int

  // Position (for map)
  worldPositionX: float
  worldPositionZ: float

  // Status
  driverStatus: int
  pitStatus: int
  penalties: int
  warnings: int
}
```

---

## 🎨 UI/UX Enhancements

### **Dark Theme CSS**

Professional color palette from reference app:
```css
:root {
  --bg-primary: #2b2b2b;
  --bg-secondary: #333;
  --bg-card: #1a1f2e;
  --text-primary: #ffffff;
  --text-secondary: #a0a0a0;
  --border-color: #2a2f3e;
  --grid-line: #444;
}
```

---

### **Team Colors**

Color-code driver names by F1 team (24 teams supported):
- Mercedes: `#00D2BE`
- Red Bull: `#0600EF`
- Ferrari: `#DC0000`
- McLaren: `#FF8700`
- Alpine: `#0090FF`
- Aston Martin: `#006F62`
- And 18 more teams...

---

### **Emoji Status Indicators**

Quick visual scanning:

**Weather:**
- ☀️ Clear
- 🌥️ Light Cloud
- ☁️ Overcast
- 🌦️ Light Rain
- 🌧️ Heavy Rain
- ⛈️ Storm

**Tyres:**
- 🔴 Soft
- 🟡 Medium
- ⚪ Hard
- 🟢 Intermediate
- 🔵 Wet

**Flags:**
- 🟢 Green
- 🟡 Yellow
- 🔴 Red
- ⚪ White

**Trends:**
- 🔼 Rising
- 🔽 Falling
- ▶️ Stable

---

## 🔧 Technical Features

### **Multi-Version Parser Support**

The reference app supports F1 25, F1 24, F1 23, and F1 22 protocols with separate parser modules:
- `parser2025.py` (967 lines)
- `parser2024.py` (934 lines)
- `parser2023.py` (830 lines)
- `parser2022.py` (762 lines)

**For Our Project:** Could add backward compatibility if needed

---

### **UDP Redirect Capability**

Forward UDP packets to another IP/port - useful for:
- Sharing telemetry with multiple machines
- Recording sessions
- Debugging

**Configuration:**
```json
{
  "redirect_active": 1,
  "ip_address": "192.168.1.100",
  "redirect_port": "20776"
}
```

---

### **Port Selection UI**

Dynamic port configuration without restarting:
- Port range validation (1000-65536)
- Persistent settings saved to JSON
- Live socket rebinding

---

### **Persistent Settings**

Save configuration to `settings.json`:
```json
{
  "port": "20777",
  "redirect_active": 0,
  "ip_address": "127.0.0.1",
  "redirect_port": "20776",
  "theme": "dark",
  "rig_a_port": 20777,
  "rig_b_port": 20778
}
```

---

## 🚀 Dual-Rig Specific Ideas

### **Side-by-Side Comparison Mode**

Filter multi-driver tables to just our 2 rigs:
- Compare every metric side-by-side
- Highlight which driver is faster (green vs red)
- Show deltas: "Driver B is 0.3s faster"

---

### **Unified Track Map**

Show both drivers on the same track map:
- Different colored markers (🔴 Rig 1, 🔵 Rig 2)
- Distance between them displayed
- Who's ahead/behind
- Track progress percentage

---

### **Relative Performance Dashboard**

Metrics:
- Who has better sector times
- Who has better tyre management (less wear)
- Who has better fuel efficiency
- Who is faster in speed traps
- Who has cleaner lap (fewer warnings/penalties)

**Display:** Winner/loser icons or color highlighting

---

## 📊 Packet Data We're Currently Missing

The reference app decodes packet types we might not be using:

### **PacketCarSetup (ID 5)**
- Front wing aero
- Rear wing aero
- Differential settings
- Suspension geometry
- Brake pressure/bias

### **PacketEvent (ID 3)**
Event types:
- `FTLP` - Fastest Lap
- `RTMT` - Retirement
- `DRSE` - DRS Enabled
- `DRSD` - DRS Disabled
- `LGOT` - Lights Out
- `CHQF` - Chequered Flag
- And 20+ more event codes

### **PacketMotionExData (ID 13)**
- Wheel speed
- Wheel slip ratio/angle
- Suspension position/velocity/acceleration
- Angular velocity (pitch/yaw/roll)
- Ride height (front left/right, rear left/right)
- Local velocity (x/y/z)

### **PacketParticipants (ID 4)**
- Driver names
- Team IDs
- AI vs Human flag
- Network ID
- Race number

### **PacketSessionHistory (ID 11)**
- Historical lap time data
- Tyre compound history
- Lap flags (valid/invalid)

---

## 🎯 Top 10 Priority Recommendations

**Ranked by implementation value for dual-rig dashboard:**

### 1. **Track Map Visualization** ⭐⭐⭐
- **Impact:** Very High
- **Difficulty:** Medium
- **Why:** Most impressive visual, perfect for comparing two drivers spatially

### 2. **Multi-Tab Organization** ⭐⭐⭐
- **Impact:** High
- **Difficulty:** Low
- **Why:** Better UX than one long scrolling page

### 3. **Sector Time Analysis** ⭐⭐⭐
- **Impact:** High
- **Difficulty:** Low
- **Why:** Easy to implement, high value for driver comparison

### 4. **Race Director Event Log** ⭐⭐
- **Impact:** Medium-High
- **Difficulty:** Medium
- **Why:** Helps track key race moments

### 5. **Tyre Compound & Age Display** ⭐⭐
- **Impact:** Medium
- **Difficulty:** Low
- **Why:** Currently missing basic info

### 6. **ERS/Fuel Management Enhanced** ⭐⭐
- **Impact:** Medium
- **Difficulty:** Low
- **Why:** More detailed power unit monitoring

### 7. **Network Diagnostics Tab** ⭐⭐
- **Impact:** High (for debugging)
- **Difficulty:** Low
- **Why:** Critical for ensuring both rigs are connected properly

### 8. **Speed Trap Analytics** ⭐
- **Impact:** Medium
- **Difficulty:** Low
- **Why:** Fun comparison metric

### 9. **Weather Forecast Display** ⭐
- **Impact:** Low-Medium
- **Difficulty:** Low
- **Why:** Nice-to-have for strategy

### 10. **Custom Dark Theme Polish** ⭐
- **Impact:** Medium (UX)
- **Difficulty:** Low
- **Why:** Professional look and feel

---

## 📐 Track Map Implementation Details

### **Data Structure**

Track files are CSV format with racing line coordinates:
```
distance,z_coordinate,x_coordinate,y_coordinate,unknown,unknown
0.0,-3050.5,650.2,0.0,0,0
10.5,-3045.0,655.8,0.0,0,0
...
```

### **Tracks Available (32+)**
- Melbourne, Paul Ricard, Shanghai, Sakhir, Barcelona
- Monaco, Montreal, Silverstone, Hockenheim, Hungaroring
- Spa, Monza, Singapore, Suzuka, Abu Dhabi, Austin
- Brazil, Austria, Sochi, Mexico, Baku, Jeddah, Miami
- Las Vegas, Losail, Imola, Portimao, Zandvoort
- Plus short layouts for several circuits

### **Rendering Algorithm**

```python
1. Load track CSV based on trackId from session packet
2. Parse X/Z coordinates (ignore Y, it's elevation)
3. Calculate bounding box (min_x, max_x, min_z, max_z)
4. Scale to canvas size with padding:
   scale_x = (canvas_width - 2*padding) / (max_x - min_x)
   scale_z = (canvas_height - 2*padding) / (max_z - min_z)
5. Draw racing line as connected polyline
6. Overlay marshal zones as colored polygons
7. Draw car positions as circles at (worldPositionX, worldPositionZ)
8. Update positions every frame
```

### **Marshal Zones**

From session packet - 21 zones per track:
```python
{
  "start": 0.0,      # Start distance fraction
  "flag": 0,         # 0=None, 1=Green, 2=Blue, 3=Yellow, 4=Red
}
```

**Color mapping:**
- Green: `#2ecc71`
- Yellow: `#f39c12`
- Red: `#e74c3c`
- Blue: `#3498db`
- None: `rgba(255,255,255,0.1)`

---

## 🔍 Code Quality Observations

### **Strengths of Reference App:**
- Clean separation of concerns (parsers, models, views)
- Comprehensive packet parsing (4 game versions)
- Thread-safe architecture (QThread for socket)
- Professional UI with custom delegates
- Extensive data validation

### **Areas for Improvement:**
- Some TODO items in code (speed trap display incomplete)
- Weather forecast sampling bug at 100%
- Map alignment issues on some tracks
- Limited documentation in code comments

---

## 💡 Adaptation Strategy for Web Dashboard

Since reference app is Qt/PySide6 desktop and ours is Flask/WebSocket web:

### **1. Track Map → HTML5 Canvas**
- Replace QPainter with Canvas 2D API
- Load track CSVs via static files
- Render with JavaScript
- Update via WebSocket messages

### **2. Table Models → HTML Tables**
- Replace QAbstractTableModel with Bootstrap tables
- Update via JavaScript DOM manipulation
- Use CSS for color coding

### **3. Threading → WebSocket**
- Replace QThread with background Flask-SocketIO
- Emit events instead of Qt signals
- Client-side updates via socket.on()

### **4. Styling → CSS**
- Convert Qt stylesheet to web CSS
- Use CSS Grid/Flexbox instead of Qt layouts
- Maintain same color scheme

---

## 📋 Implementation Checklist

### **Phase 1: Track Map (Week 1)**
- [ ] Copy track CSV files from reference app
- [ ] Create track map HTML5 Canvas component
- [ ] Implement scaling algorithm in JavaScript
- [ ] Add car position rendering
- [ ] Connect to motion packet WebSocket stream
- [ ] Add track auto-detection from session packet

### **Phase 2: Enhanced Telemetry (Week 2)**
- [ ] Add sector time display (S1/S2/S3)
- [ ] Add tyre compound and age
- [ ] Enhance ERS display (mode + color interpolation)
- [ ] Add fuel remaining in laps calculation
- [ ] Implement quad layout for tyre data

### **Phase 3: Event System (Week 3)**
- [ ] Decode event packets (ID 3)
- [ ] Create race director event log component
- [ ] Add event notification system
- [ ] Implement event filtering

### **Phase 4: Multi-Tab UI (Week 4)**
- [ ] Reorganize dashboard into tabs
- [ ] Overview tab (current main view)
- [ ] Map tab (track visualization)
- [ ] Events tab (race director)
- [ ] Diagnostics tab (packet rates)

### **Phase 5: Polish (Week 5)**
- [ ] Professional dark theme
- [ ] Team color coding
- [ ] Emoji status indicators
- [ ] Performance optimizations
- [ ] Mobile responsive design

---

## 🎓 Key Learnings

### **What Works Well in Reference App:**
1. Multi-tab organization reduces cognitive load
2. Color interpolation provides instant visual feedback
3. Track map adds critical spatial context
4. Event log captures key moments without manual tracking
5. Packet diagnostics essential for debugging
6. Player state object simplifies data management
7. Quad layout elegant for 4-value displays (tyres)

### **What to Avoid:**
1. Don't over-engineer single-user features (our app is single-user)
2. Don't implement unused packet types initially (focus on high-value)
3. Don't sacrifice performance for visual polish (60fps minimum)

### **Perfect for Dual-Rig:**
1. Track map showing both drivers simultaneously
2. Side-by-side comparison tables
3. Relative performance metrics
4. Network diagnostics to verify both connections
5. Unified event log for both drivers

---

## 📚 Resources

### **Reference App Structure:**
```
f1-25-telemetry-application-main/
├── Telemetry.py                 # Entry point
├── src/
│   ├── windows/
│   │   ├── main_window.py       # 9-tab UI
│   │   └── SocketThread.py      # UDP receiver
│   ├── table_models/            # 9 table models
│   ├── packet_processing/
│   │   ├── Player.py            # Driver state
│   │   ├── Session.py           # Race state
│   │   └── packet_management.py # Packet router
│   └── parsers/
│       ├── parser2025.py        # F1 25 protocol
│       └── parser202X.py        # Other versions
├── tracks/                      # 32+ track CSV files
├── style.css                    # Dark theme
└── settings.txt                 # JSON config
```

### **Our Project Structure:**
```
aicentre-f1-local/
├── src/
│   ├── app_dual_rig.py          # Flask + SocketIO
│   ├── receiver_multi.py        # UDP receiver
│   ├── telemetry_gateway.py     # Multi-rig manager
│   └── websocket_publisher.py   # Real-time broadcast
├── templates/
│   └── dual_rig_dashboard.html  # Web UI
├── static/
│   ├── js/dual-rig-dashboard.js
│   └── css/dual-rig-style.css
└── scripts/
    └── run_dual_dashboard.py    # Launcher
```

---

## 🎬 Conclusion

The reference F1 25 telemetry application provides a wealth of features we can adapt for our dual-rig web dashboard. The most impactful additions would be:

1. **Track map visualization** - Spatial context for both drivers
2. **Sector time analysis** - Easy driver comparison
3. **Event logging** - Automated race moment tracking
4. **Multi-tab organization** - Better information architecture

These features align perfectly with our dual-rig use case and can be implemented incrementally without disrupting existing functionality.

**Next Steps:** Begin with track map implementation as it provides the highest visual impact and is well-documented in the reference codebase.

---

**Document Version:** 1.0
**Author:** Claude Code Analysis
**Last Updated:** 2025-10-21
