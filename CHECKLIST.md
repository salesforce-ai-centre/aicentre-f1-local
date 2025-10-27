# Installation Checklist

Use this checklist to ensure everything is set up correctly.

## ☑️ Host PC (MacBook) Setup

- [ ] Repository cloned to `~/Developer/aicentre-f1-local`
- [ ] Python dependencies installed (`pip install -r config/requirements.txt`)
- [ ] Directories created (`mkdir -p data logs`)
- [ ] System starts successfully (`./scripts/start_mac.sh`)
- [ ] Flask accessible at http://localhost:8080/
- [ ] UDP receivers running on ports 20777 and 20778

## ☑️ Sim 1 PC Setup (192.168.8.22)

- [ ] Can SSH from host (`ssh sim1admin@192.168.8.22`)
- [ ] wmctrl installed (`which wmctrl`)
- [ ] xdotool installed (`which xdotool`)
- [ ] unclutter installed (`which unclutter`)
- [ ] Chrome installed
- [ ] F1 game installed
- [ ] F1 game UDP configured (IP: 172.18.159.209, Port: 20777)
- [ ] Chrome autostart configured (`~/.config/autostart/f1-attract.desktop`)
- [ ] Attract screen loads on boot (http://172.18.159.209:8080/attract?rig=1)
- [ ] Mouse cursor hides automatically

## ☑️ Sim 2 PC Setup (192.168.8.21)

- [ ] Can SSH from host (`ssh sim2admin@192.168.8.21`)
- [ ] wmctrl installed (`which wmctrl`)
- [ ] xdotool installed (`which xdotool`)
- [ ] unclutter installed (`which unclutter`)
- [ ] Chrome installed
- [ ] F1 game installed
- [ ] F1 game UDP configured (IP: 172.18.159.209, Port: 20778)
- [ ] Chrome autostart configured (`~/.config/autostart/f1-attract.desktop`)
- [ ] Attract screen loads on boot (http://172.18.159.209:8080/attract?rig=2)
- [ ] Mouse cursor hides automatically

## ☑️ Network Connectivity

- [ ] Host can ping Sim 1 (`ping 192.168.8.22`)
- [ ] Host can ping Sim 2 (`ping 192.168.8.21`)
- [ ] Sim 1 can ping Host (`ping 172.18.159.209`)
- [ ] Sim 2 can ping Host (`ping 172.18.159.209`)
- [ ] Sim 1 can access HTTP (`curl http://172.18.159.209:8080/`)
- [ ] Sim 2 can access HTTP (`curl http://172.18.159.209:8080/`)
- [ ] UDP port 20777 listening on host (`lsof -i UDP:20777`)
- [ ] UDP port 20778 listening on host (`lsof -i UDP:20778`)

## ☑️ SSH Configuration (Optional)

- [ ] SSH key exists on host (`ls ~/.ssh/id_rsa`)
- [ ] SSH key copied to Sim 1 (`ssh-copy-id sim1admin@192.168.8.22`)
- [ ] SSH key copied to Sim 2 (`ssh-copy-id sim2admin@192.168.8.21`)
- [ ] Passwordless SSH to Sim 1 works
- [ ] Passwordless SSH to Sim 2 works

## ☑️ Stream Deck Setup (Optional)

- [ ] Stream Deck software installed
- [ ] START button configured (http://localhost:8080/api/control/start-race)
- [ ] STOP button configured (http://localhost:8080/api/control/stop-race)
- [ ] RESTART button configured (http://localhost:8080/api/control/restart)

## ☑️ Functional Tests

### Test 1: QR Code Registration
- [ ] QR code visible on Sim 1 attract screen
- [ ] QR code scans successfully on phone
- [ ] Registration form loads
- [ ] Form submits successfully
- [ ] Thank you page appears on phone
- [ ] "GAME START!" appears on Sim 1 screen
- [ ] After 3 seconds, redirects to dual dashboard

### Test 2: Telemetry Flow
- [ ] Start F1 game on Sim 1
- [ ] Begin a race in F1 game
- [ ] Receiver logs show packet data (`tail -f logs/receiver-rig1.log`)
- [ ] Dual dashboard shows live telemetry
- [ ] Speed, RPM, lap times updating in real-time

### Test 3: Stream Deck Controls
- [ ] START button switches Sim 1 to F1 game
- [ ] START button switches Sim 2 to F1 game
- [ ] STOP button completes sessions
- [ ] Results screens appear
- [ ] RESTART button returns to attract screens

### Test 4: Session Management
- [ ] Create session via QR code
- [ ] Session appears in database (`curl http://localhost:8080/api/session/active/1`)
- [ ] Complete session (`curl -X POST http://localhost:8080/api/session/{id}/complete`)
- [ ] Session status changes to "Completed"
- [ ] Leaderboards update (`curl http://localhost:8080/api/leaderboard/daily`)

## ☑️ Daily Operations

### Morning Startup
- [ ] Turn on all 3 PCs
- [ ] Sims auto-load attract screens
- [ ] F1 games running in background on both sims
- [ ] Run `./scripts/start_mac.sh` on host
- [ ] Verify Flask server running
- [ ] Verify both receivers running
- [ ] Check logs for errors

### During Event
- [ ] Participants scan QR codes
- [ ] Operator presses START when ready
- [ ] Race proceeds with live telemetry
- [ ] Operator presses STOP when finished
- [ ] Results displayed
- [ ] Operator presses RESTART for next race

### End of Day
- [ ] Run `./scripts/stop_mac.sh` on host
- [ ] Close F1 games on both sims
- [ ] (Optional) Backup database (`cp data/sessions.db data/backup/`)
- [ ] Turn off all PCs

## ☑️ Troubleshooting Guide

### Problem: No telemetry data
- [ ] Check F1 game UDP settings
- [ ] Verify IP and port configuration
- [ ] Check receiver logs (`tail -f logs/receiver-rig*.log`)
- [ ] Test UDP connection (`sudo tcpdump -i any udp port 20777`)

### Problem: Attract screen not loading
- [ ] Check Chrome is running (`ps aux | grep chrome`)
- [ ] Test URL manually (`curl http://172.18.159.209:8080/attract?rig=1`)
- [ ] Check autostart file (`cat ~/.config/autostart/f1-attract.desktop`)
- [ ] Check for JavaScript errors (F12 in browser)

### Problem: Stream Deck not working
- [ ] Test API manually (`curl -X POST http://localhost:8080/api/control/start-race`)
- [ ] Check Flask logs (`tail -f logs/flask.log`)
- [ ] Verify SSH works (`ssh sim1admin@192.168.8.22 "echo test"`)
- [ ] Check wmctrl installed on sims

### Problem: Sessions not completing
- [ ] Check session exists (`curl http://localhost:8080/api/session/active/1`)
- [ ] Manually complete (`./scripts/reset_session.sh`)
- [ ] Check Flask logs for errors
- [ ] Verify database file exists (`ls -lh data/sessions.db`)

## ✅ System Ready!

If all checkboxes are complete, your F1 simulator system is fully operational!

**Next steps:**
1. Review [QUICKSTART.md](QUICKSTART.md) for daily operations
2. Test with real participants
3. Configure internet access for external QR codes (see [DEPLOYMENT.md](docs/DEPLOYMENT.md))
4. Enjoy! 🏁
