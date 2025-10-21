# Testing Dual-Rig UDP Reception

## 🎯 Milestone 1: Receive Data from Two Sim PCs

**Objective:** Verify your host machine can receive F1 25 UDP telemetry from both sim PCs simultaneously.

---

## Prerequisites

- [ ] Two PCs with F1 25 installed (Sim PC A and Sim PC B)
- [ ] One host PC (this machine) to receive telemetry
- [ ] All three PCs on the same network (Wi-Fi or Ethernet)
- [ ] Python 3.9+ installed on host PC

---

## Step-by-Step Test Procedure

### 1. Find Your Host PC's IP Address

**On this machine, run:**

```bash
# macOS/Linux
ipconfig getifaddr en0  # If using Wi-Fi
# or
ipconfig getifaddr en1  # If using Ethernet

# Alternative (shows all)
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Example output:** `192.168.1.100`

**✍️ Write down this IP address: ________________**

---

### 2. Configure Sim PC A (RIG A)

On your **first sim PC**:

1. Launch F1 25
2. Navigate to: **Game Options → Settings → Telemetry Settings**
3. Set the following:

| Setting | Value |
|---------|-------|
| UDP Telemetry | **ON** |
| UDP Format | **2025** |
| UDP Send Rate | **60 Hz** |
| Broadcast Mode | **OFF** |
| IP Address | **`<your host IP>`** (e.g., 192.168.1.100) |
| UDP Port | **20777** |

4. Save settings
5. Start a **practice session** or **time trial**

---

### 3. Configure Sim PC B (RIG B)

On your **second sim PC**:

1. Launch F1 25
2. Navigate to: **Game Options → Settings → Telemetry Settings**
3. Set the following:

| Setting | Value |
|---------|-------|
| UDP Telemetry | **ON** |
| UDP Format | **2025** |
| UDP Send Rate | **60 Hz** |
| Broadcast Mode | **OFF** |
| IP Address | **`<your host IP>`** (e.g., 192.168.1.100) |
| UDP Port | **20778** ⚠️ **Different port!** |

4. Save settings
5. Start a **practice session** or **time trial**

---

### 4. Start the Telemetry Receiver on Host PC

**On this machine:**

```bash
# Navigate to project directory
cd /Users/jacob.berry/Developer/aicentre-f1-local

# Run the test receiver
python3 scripts/test_dual_receiver.py
```

**Expected output:**

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

---

### 5. Verify Data Reception

**Within 2-3 seconds**, you should see telemetry data updating:

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

## ✅ Success Criteria

- [ ] You see data from **RIG_A** (port 20777)
- [ ] You see data from **RIG_B** (port 20778)
- [ ] Both displays update in real-time as you drive
- [ ] Speed, RPM, gear changes reflect what's happening in-game
- [ ] No error messages in the terminal

**If all boxes are checked: 🎉 MILESTONE 1 COMPLETE!**

---

## 🔧 Troubleshooting

### Problem: No data from either rig

**Fix:**
1. Check firewall on host PC:
   ```bash
   # macOS - allow Python UDP
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add $(which python3)
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp $(which python3)
   ```

2. Verify network connectivity:
   ```bash
   # From each sim PC, ping the host
   ping 192.168.1.100
   ```

3. Make sure F1 25 is **in a session** (not menus)

### Problem: Only RIG_A shows data

**Fix:**
1. Double-check RIG_B is using **port 20778** (not 20777)
2. Verify IP address is correct on RIG_B
3. Make sure RIG_B is actually in a driving session

### Problem: Data is choppy or delayed

**Fix:**
1. Reduce send rate to 30 Hz in F1 25 settings
2. Check network bandwidth (run `iftop` or similar)
3. Make sure both sim PCs are on the same network switch/router

### Problem: Port already in use

**Fix:**
```bash
# Kill any process using the ports
lsof -ti :20777 | xargs kill
lsof -ti :20778 | xargs kill

# Then restart the receiver
python3 scripts/test_dual_receiver.py
```

---

## 📊 Performance Metrics

At 60 Hz send rate:
- **Bandwidth per rig:** ~6 KB/s
- **Total bandwidth:** ~12 KB/s
- **Expected CPU usage:** <5%
- **Expected latency:** <20ms

---

## 🐛 Debug Mode

If you're having issues, run with verbose logging:

```bash
# Set debug level
export PYTHONLOGLEVEL=DEBUG
python3 scripts/test_dual_receiver.py
```

This will show detailed packet information for debugging.

---

## Next Steps After Milestone 1

Once you confirm both rigs are working:

1. **Milestone 2:** WebSocket real-time publisher
2. **Milestone 3:** Dual-rig web dashboard UI
3. **Milestone 4:** Data Cloud integration
4. **Milestone 5:** Session analytics and replay

---

## Notes

- The test receiver displays a **simplified view** of telemetry
- Full dashboard will show all data (tyre wear, damage, fuel, etc.)
- Session UIDs are unique per session (resets when you restart)
- Frame identifiers increment continuously throughout the session

---

## Getting Help

If you're stuck:

1. Check the logs for error messages
2. Review [DUAL_RIG_SETUP.md](DUAL_RIG_SETUP.md) for detailed troubleshooting
3. Verify F1 25 telemetry settings match exactly
4. Test one rig at a time to isolate issues
