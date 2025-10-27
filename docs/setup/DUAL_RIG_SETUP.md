# Dual-Rig Setup Guide

## Quick Start: Receiving Data from Two Sim PCs

This guide will help you configure two F1 25 sim PCs to send telemetry to your host machine.

---

## Network Setup

### Step 1: Find Your Host PC's IP Address

**On your host machine (where this code runs):**

**macOS/Linux:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Windows:**
```bash
ipconfig
```

Look for your local network IP (usually starts with `192.168.` or `10.0.`)

Example: `192.168.1.100`

**Write this down - you'll need it for both sim PCs!**

---

## Sim PC Configuration

### Step 2: Configure F1 25 on Each Sim PC

Configure **both** sim PCs identically except for the UDP port:

#### **Sim PC A (RIG_A)**

1. Launch F1 25
2. Go to: **Settings → Telemetry Settings**
3. Configure:
   ```
   UDP Telemetry: ON
   UDP Format: 2025
   UDP Send Rate: 60 Hz
   Broadcast Mode: OFF
   IP Address: <YOUR HOST PC IP>    (e.g., 192.168.1.100)
   UDP Port: 20777
   ```

#### **Sim PC B (RIG_B)**

1. Launch F1 25
2. Go to: **Settings → Telemetry Settings**
3. Configure:
   ```
   UDP Telemetry: ON
   UDP Format: 2025
   UDP Send Rate: 60 Hz
   Broadcast Mode: OFF
   IP Address: <YOUR HOST PC IP>    (e.g., 192.168.1.100)
   UDP Port: 20778
   ```

**⚠️ IMPORTANT: RIG B must use port 20778 (different from RIG A!)**

---

## Testing the Setup

### Step 3: Start the Telemetry Receiver on Host PC

On your host machine:

```bash
cd /Users/jacob.berry/Developer/aicentre-f1-local
python3 scripts/test_dual_receiver.py
```

You should see:

```
================================================================================
DUAL-RIG TELEMETRY RECEIVER STARTED
================================================================================

Listening on:
  🔴 RIG A: UDP port 20777 (Driver: Driver A)
  🔵 RIG B: UDP port 20778 (Driver: Driver B)

Configure your F1 25 game on each sim PC to send UDP to:
  IP Address: <this PC's IP address>
  UDP Format: 2025
  Send Rate: 60 Hz

Press Ctrl+C to stop
================================================================================
```

### Step 4: Start F1 25 Sessions on Both Sim PCs

1. On **Sim PC A**: Start a practice session, time trial, or race
2. On **Sim PC B**: Start a practice session, time trial, or race

**They can be in different sessions - doesn't matter!**

### Step 5: Verify Data Reception

The monitor will automatically update every second showing telemetry from both rigs:

```
================================================================================
F1 25 DUAL-RIG TELEMETRY MONITOR
================================================================================
Time: 2025-10-21 15:30:45

🔴 RIG_A - Driver A
----------------------------------------
  Session: 12345678 | Frame: 5432
  Speed: 287 km/h | RPM: 11850
  Gear: 7 | Throttle: 98% | Brake: 0%
  Tyres: FL:95°C FR:97°C RL:92°C RR:94°C

🔵 RIG_B - Driver B
----------------------------------------
  Session: 87654321 | Frame: 3210
  Speed: 156 km/h | RPM: 8200
  Gear: 4 | Throttle: 45% | Brake: 12%
  Tyres: FL:82°C FR:84°C RL:80°C RR:81°C
```

---

## Troubleshooting

### No Data Received

**1. Check network connectivity**
```bash
# From Sim PC A or B, ping the host PC
ping 192.168.1.100
```

**2. Check firewall settings**

On the **host PC**, ensure UDP ports 20777 and 20778 are allowed:

**macOS:**
```bash
# Allow Python to receive UDP
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add $(which python3)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp $(which python3)
```

**Windows:**
```powershell
# Add firewall rule (run as Administrator)
New-NetFirewallRule -DisplayName "F1 Telemetry RIG A" -Direction Inbound -Protocol UDP -LocalPort 20777 -Action Allow
New-NetFirewallRule -DisplayName "F1 Telemetry RIG B" -Direction Inbound -Protocol UDP -LocalPort 20778 -Action Allow
```

**3. Verify F1 25 settings**
- Make sure "UDP Telemetry" is **ON**
- Double-check the IP address matches your host PC
- Verify the ports (20777 for RIG A, 20778 for RIG B)
- Try toggling UDP off and back on

**4. Check if ports are already in use**
```bash
# On host PC
lsof -i :20777
lsof -i :20778
```

If something is using these ports, kill it:
```bash
lsof -ti :20777 | xargs kill
lsof -ti :20778 | xargs kill
```

### Only One Rig Shows Data

**Check:**
1. Is the other sim PC actually in a session? (not in menus)
2. Did you use the correct ports? (20777 vs 20778)
3. Are both sim PCs on the same network as the host?

### Data Stops After a Few Seconds

- The game may have paused or returned to menus
- Check the session is still active
- Verify network connection is stable

### Performance Issues

If you see packet loss or delays:

1. **Reduce send rate:**
   ```
   F1 25 → Settings → Telemetry → Send Rate: 30 Hz
   ```

2. **Check network bandwidth:**
   - At 60 Hz, each rig sends ~6KB/s
   - Total: ~12KB/s for both rigs (very low bandwidth)

3. **Monitor CPU usage:**
   ```bash
   top -p $(pgrep -f test_dual_receiver)
   ```

---

## Environment Variables (Optional)

You can set driver names via environment variables:

```bash
export DRIVER_A_NAME="Lewis Hamilton"
export DRIVER_B_NAME="Max Verstappen"
python3 scripts/test_dual_receiver.py
```

Or create a `.env` file in the project root:

```bash
DRIVER_A_NAME=Lewis Hamilton
DRIVER_B_NAME=Max Verstappen
```

---

## What Packets Are Received?

The receiver captures:

- **Telemetry (Packet ID 6)**: Speed, throttle, brake, gear, RPM, tyre temps
- **Lap Data (Packet ID 2)**: Lap times, position, sector splits
- **Car Status (Packet ID 7)**: Fuel, DRS, ERS, tyre compound
- **Car Damage (Packet ID 10)**: Wing damage, engine damage, etc.
- **Session (Packet ID 1)**: Track, weather, session info

All packets are enriched with:
- `rig_id`: Which sim sent the data ("RIG_A" or "RIG_B")
- `driver_name`: Driver name from config
- `device_id`: Unique device identifier
- `timestamp_gateway`: When the host received it

---

## Next Steps

Once you confirm both rigs are sending data:

✅ **Milestone 1 Complete!** You're receiving UDP from both sim PCs.

**Next milestones:**
- [ ] Build WebSocket publisher for real-time dashboard
- [ ] Create dual-rig web dashboard UI
- [ ] Integrate Data Cloud uploader
- [ ] Add session replay and analytics

---

## Advanced: Broadcast Mode (Alternative Setup)

If you want multiple receivers (e.g., host PC + another laptop):

**F1 25 Settings (both rigs):**
```
Broadcast Mode: ON
IP Address: 255.255.255.255  (or your subnet broadcast, e.g., 192.168.1.255)
```

This broadcasts to all devices on the network. Multiple hosts can listen on the same ports.

**Note:** Broadcast mode may not work on all networks (some routers block broadcasts).

---

## Support

If you're still having issues:

1. Check the logs in the terminal
2. Verify network connectivity with `ping`
3. Try running with debug logging:
   ```bash
   python3 scripts/test_dual_receiver.py --debug
   ```

4. Check if other UDP apps work on your network
