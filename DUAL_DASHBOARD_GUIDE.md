# Dual Dashboard Guide

## Overview

The dual-rig dashboard shows **both simulators side-by-side** on a single screen, perfect for spectators or overhead displays.

## Accessing the Dual Dashboard

**URL:**
```
http://localhost:8080/dual
```

## What It Shows

### Split-Screen Layout

```
┌─────────────────────────────────────────────────────────┐
│        🏎️ Dual-Rig F1 25 Telemetry                     │
└─────────────────────────────────────────────────────────┘

┌────────────────────────┬─────────────────────────────┐
│  🔴 Sim Rig 1          │  🔵 Sim Rig 2               │
│  Driver: Alice         │  Driver: Bob                │
│  Track: Monaco         │  Track: Monaco              │
│                        │                             │
│  Speed: 287 km/h       │  Speed: 294 km/h            │
│  Gear: 6               │  Gear: 7                    │
│  RPM: 11,250           │  RPM: 12,100                │
│  Lap: 5/10             │  Lap: 5/10                  │
│  Position: 3rd         │  Position: 1st              │
│  Current: 1:34.567     │  Current: 1:32.123          │
│  Best: 1:33.456        │  Best: 1:31.987             │
│                        │                             │
│  [Tire Data]           │  [Tire Data]                │
│  [ERS/DRS Status]      │  [ERS/DRS Status]           │
│  [Damage]              │  [Damage]                   │
└────────────────────────┴─────────────────────────────┘
```

## Use Cases

### 1. Spectator Display
- Mount a large TV/monitor visible to spectators
- Shows real-time comparison of both drivers
- Great for competitive racing events

### 2. Overhead Monitor
- Display above both simulators
- Drivers can see their competitor's progress
- Adds competitive atmosphere

### 3. Streaming/Recording
- Capture both drivers in one frame
- Perfect for Twitch/YouTube content
- Shows head-to-head competition

## Features

### Live Telemetry for Both Rigs
- **Speed, Gear, RPM** - Current vehicle stats
- **Lap Times** - Current lap, last lap, best lap
- **Position** - Race position for each driver
- **Track Info** - Track name and session type
- **Tire Data** - Wear and temperatures for all tires
- **ERS/DRS** - Energy deployment and DRS status
- **Damage** - Real-time damage indicators

### Driver Names
- Automatically pulls from active sessions
- Shows "Waiting..." if no session active
- Updates when new sessions start

### Color Coding
- **Rig 1** (Left): Red theme 🔴
- **Rig 2** (Right): Blue theme 🔵

## Setup Instructions

### For Spectator Display

1. **Connect external monitor/TV**
2. **Open browser on the display**:
   ```
   http://localhost:8080/dual
   ```
3. **Press F11 for fullscreen**
4. **Done!** Both rigs now visible

### For Streaming

1. **OBS Setup**:
   - Add "Browser Source"
   - URL: `http://localhost:8080/dual`
   - Width: 1920, Height: 1080
   - Check "Refresh browser when scene becomes active"

2. **Streamlabs Setup**:
   - Add "Browser Source"
   - URL: `http://localhost:8080/dual`
   - Dimensions: 1920x1080

### Network Access

If displaying on a separate device:

1. **Find server IP**:
   ```bash
   ifconfig | grep "inet "  # macOS/Linux
   ipconfig                 # Windows
   ```

2. **Open on other device**:
   ```
   http://<SERVER_IP>:8080/dual
   ```

## Comparison with Single Dashboard

| Feature | Single (`/`) | Dual (`/dual`) |
|---------|-------------|----------------|
| View | One driver | Both drivers |
| Layout | Full screen | Split screen |
| Use Case | Individual rig | Spectator/streaming |
| Updates | Real-time SSE | Real-time SSE |
| Data Source | One UDP stream | Two UDP streams |

## Individual Rig Dashboards

For each rig's own display (not shared):

**Simulator 1:**
```
http://localhost:8080/?rig=1
```

**Simulator 2:**
```
http://localhost:8080/?rig=2
```

Or use the dual dashboard route:
```
http://localhost:8080/dual
```

## Complete Display Setup

Here's the recommended setup for a dual-rig experience:

### Simulator 1 Display
- **Attract Screen**: `http://localhost:8080/attract?rig=1`
- **During Race**: Auto-switches to individual dashboard
- **After Race**: Shows summary, returns to attract

### Simulator 2 Display
- **Attract Screen**: `http://localhost:8080/attract?rig=2`
- **During Race**: Auto-switches to individual dashboard
- **After Race**: Shows summary, returns to attract

### Overhead/Spectator Display
- **Always Shows**: `http://localhost:8080/dual`
- **Purpose**: Both drivers visible at once
- **Fullscreen**: Yes (F11)

## Troubleshooting

### "Waiting..." Shown for Both Rigs
**Cause**: No active sessions
**Solution**:
- Start a session by scanning QR code on attract screen
- Or create sessions via API

### Only One Rig Showing Data
**Cause**: Only one rig has active session
**Solution**:
- This is normal if only one person is racing
- Second rig will show "Waiting..." until someone starts

### Data Not Updating
**Cause**: F1 game not sending telemetry
**Solution**:
- Check F1 game UDP settings (port 20777)
- Verify receiver is running
- Check receiver logs for errors

### Wrong Driver Names
**Cause**: Session not started properly
**Solution**:
- Ensure QR landing page form was submitted
- Check sessions in database
- Restart sessions if needed

## API Integration

The dual dashboard automatically fetches:

```javascript
// On page load
GET /api/session/active/1  // Get Rig 1 session
GET /api/session/active/2  // Get Rig 2 session

// During race (SSE streams)
EventSource: /stream?rig=1  // Rig 1 telemetry
EventSource: /stream?rig=2  // Rig 2 telemetry
```

## Customization

The dual dashboard uses:
- **Template**: `templates/dual_rig_dashboard.html`
- **Styles**: `static/css/dual-rig-style.css`
- **JavaScript**: `static/js/dual-rig-dashboard.js`

Edit these files to customize layout, colors, or data displayed.

## Summary

✅ **Dual Dashboard**: Shows both simulators side-by-side
✅ **URL**: `http://localhost:8080/dual`
✅ **Use For**: Spectators, streaming, overhead displays
✅ **Real-Time**: Live telemetry from both rigs
✅ **Auto-Updates**: Driver names from active sessions

**Perfect for competitive racing events!** 🏎️🏎️
