# F1 Simulator System - Quick Start Guide

## 🚀 Getting Started in 5 Steps

### Step 1: Start the Host (Your MacBook)

```bash
cd ~/Developer/aicentre-f1-local
./scripts/start_mac.sh
```

✅ You should see: Flask server + 2 receivers running

---

### Step 2: Deploy to Sim 1

```bash
./scripts/deploy_to_sim.sh 1
```

This will:
- Install required software (wmctrl, xdotool, unclutter)
- Configure Chrome to auto-start attract screen
- Set up mouse cursor hiding

**Manual step:** Configure F1 game on Sim 1:
- Settings → Telemetry → UDP
- IP: `172.18.159.209`
- Port: `20777`

---

### Step 3: Deploy to Sim 2

```bash
./scripts/deploy_to_sim.sh 2
```

**Manual step:** Configure F1 game on Sim 2:
- Settings → Telemetry → UDP
- IP: `172.18.159.209`
- Port: `20778`

---

### Step 4: Reboot Both Sims

```bash
# Reboot Sim 1
ssh sim1admin@192.168.8.22 "sudo reboot"

# Reboot Sim 2
ssh sim2admin@192.168.8.21 "sudo reboot"
```

After reboot:
- ✅ Chrome should show attract screen with QR code
- ✅ F1 game should be ready in background

---

### Step 4.5: Deploy Chrome Extension (For Automatic Window Switching)

The Chrome extension enables **fully automatic window switching** - the sims will switch from attract screen to F1 game without players pressing anything!

```bash
# Deploy to Sim 1
./scripts/deploy_chrome_extension.sh 1

# Deploy to Sim 2
./scripts/deploy_chrome_extension.sh 2
```

This installs:
- wmctrl/xdotool (window management tools)
- Native messaging host (Python script)
- Native messaging manifest

**Manual steps on each Sim:**

1. Copy extension folder to Sim:
   ```bash
   scp -r chrome-extension sim1admin@192.168.8.22:~/chrome-extension
   scp -r chrome-extension sim2admin@192.168.8.21:~/chrome-extension
   ```

2. On Sim PC, open Chrome → `chrome://extensions/`

3. Enable "Developer mode" (toggle top-right)

4. Click "Load unpacked" → Select `~/chrome-extension`

5. **Copy the Extension ID** (looks like: `abcdefghijklmnopqrstuvwxyz`)

6. Update manifest with Extension ID:
   ```bash
   nano ~/.config/google-chrome/NativeMessagingHosts/com.f1.windowswitcher.json
   # Replace EXTENSION_ID_WILL_BE_FILLED with your actual ID
   ```

7. Test in Chrome console (F12) on attract screen:
   ```javascript
   F1Controller.test()
   F1Controller.switchToGame()
   ```

   ✅ If window switches to F1 game, installation successful!

📚 **Detailed Guide:** See [chrome-extension/README.md](chrome-extension/README.md)

---

### Step 5: Test It!

1. **Scan QR code** on Sim 1 with your phone
2. **Enter your name** and accept terms
3. **Sim screen shows** "GAME START!"
4. **Press START** on Stream Deck (or run: `curl -X POST http://localhost:8080/api/control/start-race`)
5. **Race!** Both sims switch to F1 game, telemetry flows to dual dashboard

---

## 📋 Daily Operations

### Morning Startup

```bash
# On Host PC
cd ~/Developer/aicentre-f1-local
./scripts/start_mac.sh
```

Sims auto-start Chrome when turned on.

### Control the Race

**Option A: Stream Deck Buttons**
- 🟢 START - Switch to game
- 🔴 STOP - End race, show results
- 🟡 RESTART - Back to attract screens

**Option B: Command Line**
```bash
# Start race
curl -X POST http://localhost:8080/api/control/start-race

# Stop race
curl -X POST http://localhost:8080/api/control/stop-race

# Restart
curl -X POST http://localhost:8080/api/control/restart
```

### End of Day Shutdown

```bash
# On Host PC
./scripts/stop_mac.sh
```

Turn off sims.

---

## 🔧 Common Commands

### View Logs
```bash
# All logs
tail -f logs/*.log

# Just Flask
tail -f logs/flask.log

# Just receivers
tail -f logs/receiver-rig*.log
```

### Reset Sessions
```bash
./scripts/reset_session.sh
```

### Check What's Running
```bash
# On Host
ps aux | grep python

# Ports in use
lsof -i :8080
lsof -i :20777
lsof -i :20778
```

### Test Network
```bash
# From Host to Sims
ping 192.168.8.22  # Sim 1
ping 192.168.8.21  # Sim 2

# HTTP test
curl http://localhost:8080/
```

---

## 📚 Full Documentation

- **[INSTALLATION.md](docs/INSTALLATION.md)** - Complete setup guide
- **[STREAM_DECK_CONTROL.md](docs/STREAM_DECK_CONTROL.md)** - Stream Deck configuration
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Network and deployment details
- **[CLAUDE.md](CLAUDE.md)** - System architecture and codebase guide

---

## 🆘 Troubleshooting

### Problem: No telemetry data

1. Check F1 game UDP settings
2. Check receiver logs: `tail -f logs/receiver-rig1.log`
3. Test UDP: `sudo tcpdump -i any udp port 20777`

### Problem: Sims don't switch windows

1. Test SSH: `ssh sim1admin@192.168.8.22 "echo test"`
2. Check wmctrl: `ssh sim1admin@192.168.8.22 "which wmctrl"`
3. Manual test: `ssh sim1admin@192.168.8.22 "DISPLAY=:0 wmctrl -l"`

### Problem: Attract screen doesn't load

1. Check Chrome: `ssh sim1admin@192.168.8.22 "ps aux | grep chrome"`
2. Test URL: `curl http://172.18.159.209:8080/attract?rig=1`
3. Check autostart: `ssh sim1admin@192.168.8.22 "cat ~/.config/autostart/f1-attract.desktop"`

---

## 🌐 Important URLs

| What | URL |
|------|-----|
| Welcome/Admin | http://172.18.159.209:8080/ |
| Sim 1 Attract | http://172.18.159.209:8080/attract?rig=1 |
| Sim 2 Attract | http://172.18.159.209:8080/attract?rig=2 |
| Dual Dashboard | http://172.18.159.209:8080/dual |

---

## ⚙️ Configuration

### Network
- **Host (MacBook)**: 172.18.159.209
- **Sim 1**: 192.168.8.22 (sim1admin / Salesforce1)
- **Sim 2**: 192.168.8.21 (sim2admin / Salesforce1)

### Ports
- **Flask**: 8080
- **Rig 1 UDP**: 20777
- **Rig 2 UDP**: 20778

---

## 🎯 Next Steps

1. ✅ Complete Step 1-5 above
2. Configure Stream Deck (see [STREAM_DECK_CONTROL.md](docs/STREAM_DECK_CONTROL.md))
3. Test complete flow with real participants
4. Set up internet access for mobile QR codes (see [DEPLOYMENT.md](docs/DEPLOYMENT.md))

---

**That's it! Your F1 simulator system is ready to go! 🏁**
