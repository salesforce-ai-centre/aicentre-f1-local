# Complete Installation Guide - 3 Machine Setup

## System Overview

This guide will help you install and configure the F1 simulator system across 3 machines:

- **Host PC (MacBook)**: `172.18.159.209` - Runs Flask server, receivers, database
- **Sim 1 PC**: `192.168.8.22` - Runs F1 game + Chrome browser
- **Sim 2 PC**: `192.168.8.21` - Runs F1 game + Chrome browser

---

## Part 1: Host PC (MacBook) Setup

### 1.1 Clone Repository

```bash
cd ~/Developer
git clone <your-repo-url> aicentre-f1-local
cd aicentre-f1-local
```

### 1.2 Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r config/requirements.txt
```

### 1.3 Create Required Directories

```bash
mkdir -p data logs
```

### 1.4 Start the System

```bash
# Start Flask + both receivers
./scripts/start_mac.sh
```

You should see:
```
✓ Flask Server (PID: XXXXX)
✓ Rig 1 Receiver (PID: XXXXX)
✓ Rig 2 Receiver (PID: XXXXX)

URLs:
  Welcome Page:    http://localhost:8080/
  Sim 1 Attract:   http://172.18.159.209:8080/attract?rig=1
  Sim 2 Attract:   http://172.18.159.209:8080/attract?rig=2
  Dual Dashboard:  http://172.18.159.209:8080/dual
```

### 1.5 Verify It's Working

Open browser to: http://localhost:8080/

You should see the welcome screen with navigation links.

### 1.6 Make Scripts Executable

```bash
chmod +x scripts/*.sh
```

---

## Part 2: Sim PC 1 Setup (192.168.8.22)

### 2.1 SSH into Sim 1

```bash
ssh sim1admin@192.168.8.22
# Password: Salesforce1
```

### 2.2 Install Required Software

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install window management tools
sudo apt install -y wmctrl xdotool

# Install Chrome (if not already installed)
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt install -f  # Fix dependencies if needed

# Install unclutter (hide mouse cursor)
sudo apt install -y unclutter
```

### 2.3 Configure F1 Game

1. Launch F1 25 (or F1 24)
2. Go to **Settings → Telemetry Settings**
3. Configure:
   - **UDP Telemetry**: ON
   - **UDP IP Address**: `172.18.159.209` (Host MacBook)
   - **UDP Port**: `20777`
   - **UDP Format**: F1 2025 (or F1 2024)
   - **UDP Broadcast Mode**: ON
4. Save and exit to main menu (keep game running)

### 2.4 Set Up Browser Auto-Start

Create autostart file:

```bash
mkdir -p ~/.config/autostart
nano ~/.config/autostart/f1-attract.desktop
```

Add this content:

```ini
[Desktop Entry]
Type=Application
Name=F1 Attract Screen - Rig 1
Exec=google-chrome --kiosk --incognito --disable-infobars --noerrdialogs --disable-session-crashed-bubble http://172.18.159.209:8080/attract?rig=1
Terminal=false
```

Save with `Ctrl+O`, `Enter`, `Ctrl+X`

### 2.5 Hide Mouse Cursor (Optional)

```bash
nano ~/.config/autostart/hide-cursor.desktop
```

Add:

```ini
[Desktop Entry]
Type=Application
Name=Hide Mouse Cursor
Exec=/usr/bin/unclutter -idle 0.1
Terminal=false
```

### 2.6 Test the Browser

```bash
google-chrome --kiosk http://172.18.159.209:8080/attract?rig=1
```

You should see the attract screen in fullscreen with QR code.

Press `Alt+F4` to close for now.

### 2.7 Reboot to Test Auto-Start

```bash
sudo reboot
```

After reboot:
- Chrome should auto-launch in kiosk mode
- Attract screen should be visible
- Mouse cursor should be hidden

---

## Part 3: Sim PC 2 Setup (192.168.8.21)

**Repeat all steps from Part 2, but with these differences:**

### 3.1 SSH into Sim 2

```bash
ssh sim2admin@192.168.8.21
```

### 3.2 F1 Game Configuration

- **UDP Port**: `20778` (different from Sim 1!)
- **UDP IP**: `172.18.159.209` (same as Sim 1)

### 3.3 Browser Auto-Start Configuration

In the `.desktop` file, change the URL:

```ini
Exec=google-chrome --kiosk --incognito --disable-infobars --noerrdialogs --disable-session-crashed-bubble http://172.18.159.209:8080/attract?rig=2
```

Note: `?rig=2` instead of `?rig=1`

---

## Part 4: Network Configuration

### 4.1 Verify Network Connectivity

From Host PC (MacBook):

```bash
# Ping Sim 1
ping 192.168.8.22

# Ping Sim 2
ping 192.168.8.21
```

From Sim 1:

```bash
# Ping Host
ping 172.18.159.209

# Test HTTP
curl http://172.18.159.209:8080/
```

From Sim 2:

```bash
# Ping Host
ping 172.18.159.209

# Test HTTP
curl http://172.18.159.209:8080/
```

### 4.2 Test UDP Connectivity

On Host PC, check if receivers are listening:

```bash
lsof -i UDP:20777
lsof -i UDP:20778
```

You should see Python processes on both ports.

---

## Part 5: SSH Key Setup (Optional but Recommended)

This allows Stream Deck to control the sims without passwords.

### 5.1 Generate SSH Key on Host

```bash
# Check if key exists
ls ~/.ssh/id_rsa

# If not, generate one
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
```

### 5.2 Copy Key to Both Sims

```bash
# Copy to Sim 1
ssh-copy-id sim1admin@192.168.8.22

# Copy to Sim 2
ssh-copy-id sim2admin@192.168.8.21
```

Enter password `Salesforce1` when prompted.

### 5.3 Test Passwordless SSH

```bash
# Test Sim 1
ssh sim1admin@192.168.8.22 "echo 'SSH works!'"

# Test Sim 2
ssh sim2admin@192.168.8.21 "echo 'SSH works!'"
```

Should connect without asking for password.

---

## Part 6: Stream Deck Setup (Optional)

### 6.1 Install Stream Deck Software

Download and install from: https://www.elgato.com/downloads

### 6.2 Configure Buttons

**Button 1: START RACE (Green)**

- Action: System → Website
- URL: `http://localhost:8080/api/control/start-race`
- Method: POST
- Icon: Green background with "START 🏁"

**Button 2: STOP RACE (Red)**

- Action: System → Website
- URL: `http://localhost:8080/api/control/stop-race`
- Method: POST
- Icon: Red background with "STOP ⏹️"

**Button 3: RESTART (Yellow)**

- Action: System → Website
- URL: `http://localhost:8080/api/control/restart`
- Method: POST
- Icon: Yellow background with "RESTART 🔄"

---

## Part 7: Testing the Complete System

### 7.1 Initial State Check

**Host PC:**
- [ ] Flask server running (`./scripts/start_mac.sh`)
- [ ] Check: `curl http://localhost:8080/` returns HTML

**Sim 1:**
- [ ] F1 game running in background
- [ ] Chrome showing attract screen with QR code
- [ ] Telemetry configured (IP: 172.18.159.209, Port: 20777)

**Sim 2:**
- [ ] F1 game running in background
- [ ] Chrome showing attract screen with QR code
- [ ] Telemetry configured (IP: 172.18.159.209, Port: 20778)

### 7.2 Test QR Code Flow

1. Scan QR code on Sim 1 with your phone
2. Enter name: "Test Driver 1"
3. Accept terms and safety rules
4. Submit

**Expected Result:**
- Phone shows "Thank You" page
- Sim 1 screen shows "GAME START!" overlay
- After 3 seconds, redirects to dual dashboard

### 7.3 Test Telemetry

1. On Sim 1, start a race in F1 game
2. On Host PC, check receiver logs:

```bash
tail -f logs/receiver-rig1.log
```

**Expected Output:**
```
Received packet: LAP_DATA
Received packet: TELEMETRY
Received packet: CAR_STATUS
```

3. Open dual dashboard: http://localhost:8080/dual

**Expected Result:**
- Rig 1 shows live telemetry (speed, RPM, lap times)
- Rig 2 shows "Waiting..." (no driver yet)

### 7.4 Test Stream Deck Controls (or Manual)

**Start Race:**
```bash
curl -X POST http://localhost:8080/api/control/start-race
```

**Expected:**
- Both sims switch from Chrome to F1 game window

**Stop Race:**
```bash
curl -X POST http://localhost:8080/api/control/stop-race
```

**Expected:**
- Sessions marked as completed
- Results screens shown

**Restart:**
```bash
curl -X POST http://localhost:8080/api/control/restart
```

**Expected:**
- All screens return to attract screens
- System ready for next race

---

## Part 8: Troubleshooting

### Problem: Sim can't reach Host

```bash
# On Sim PC
ping 172.18.159.209
curl http://172.18.159.209:8080/
```

**Solution:** Check firewall on Host PC

### Problem: No telemetry data

**Check F1 game settings:**
- UDP enabled?
- Correct IP (172.18.159.209)?
- Correct port (20777 for Sim 1, 20778 for Sim 2)?

**Check receiver logs:**
```bash
tail -f logs/receiver-rig1.log
tail -f logs/receiver-rig2.log
```

**Test UDP:**
```bash
sudo tcpdump -i any udp port 20777
```

### Problem: Chrome doesn't auto-start on boot

**Check autostart file:**
```bash
cat ~/.config/autostart/f1-attract.desktop
```

**Test manually:**
```bash
google-chrome --kiosk http://172.18.159.209:8080/attract?rig=1
```

**Check logs:**
```bash
journalctl --user -u f1-attract
```

### Problem: Stream Deck buttons don't work

**Test API manually:**
```bash
curl -X POST http://localhost:8080/api/control/start-race
```

**Check Flask logs:**
```bash
tail -f logs/flask.log
```

**Verify SSH access:**
```bash
ssh sim1admin@192.168.8.22 "echo test"
```

---

## Part 9: Maintenance

### Start/Stop System

**Host PC:**
```bash
# Start everything
./scripts/start_mac.sh

# Stop everything
./scripts/stop_mac.sh

# Reset sessions
./scripts/reset_session.sh
```

### View Logs

```bash
# Flask server
tail -f logs/flask.log

# Rig 1 receiver
tail -f logs/receiver-rig1.log

# Rig 2 receiver
tail -f logs/receiver-rig2.log

# All logs
tail -f logs/*.log
```

### Update Code

```bash
cd ~/Developer/aicentre-f1-local
git pull
source venv/bin/activate
pip install -r config/requirements.txt
./scripts/stop_mac.sh
./scripts/start_mac.sh
```

### Backup Database

```bash
cp data/sessions.db data/sessions.db.backup-$(date +%Y%m%d)
```

### Reset Database

```bash
./scripts/stop_mac.sh
rm data/sessions.db
./scripts/start_mac.sh
```

---

## Part 10: Quick Reference

### URLs

| Screen | URL | Device |
|--------|-----|--------|
| Welcome/Admin | http://172.18.159.209:8080/ | Any |
| Sim 1 Attract | http://172.18.159.209:8080/attract?rig=1 | Sim 1 |
| Sim 2 Attract | http://172.18.159.209:8080/attract?rig=2 | Sim 2 |
| Dual Dashboard | http://172.18.159.209:8080/dual | Host |
| Registration Form | http://172.18.159.209:8080/start?rig=1 | Mobile |
| Thank You | http://172.18.159.209:8080/thank-you | Mobile |

### Ports

| Port | Service | Description |
|------|---------|-------------|
| 8080 | Flask HTTP | Web server |
| 20777 | UDP Receiver | Sim 1 telemetry |
| 20778 | UDP Receiver | Sim 2 telemetry |

### Scripts

| Script | Purpose |
|--------|---------|
| `./scripts/start_mac.sh` | Start all services |
| `./scripts/stop_mac.sh` | Stop all services |
| `./scripts/reset_session.sh` | Complete active sessions |
| `./scripts/control_start_race.sh` | Stream Deck START |
| `./scripts/control_stop_race.sh` | Stream Deck STOP |
| `./scripts/control_restart.sh` | Stream Deck RESTART |

### SSH Access

```bash
# Sim 1
ssh sim1admin@192.168.8.22

# Sim 2
ssh sim2admin@192.168.8.21

# Password for both
Salesforce1
```

---

## Part 11: Deployment Checklist

### First Time Setup

- [ ] Host: Clone repository
- [ ] Host: Install Python dependencies
- [ ] Host: Create directories (data, logs)
- [ ] Host: Start system (`./scripts/start_mac.sh`)
- [ ] Sim 1: Install wmctrl, xdotool, Chrome
- [ ] Sim 1: Configure F1 game (UDP: 172.18.159.209:20777)
- [ ] Sim 1: Set up browser autostart
- [ ] Sim 1: Reboot and verify
- [ ] Sim 2: Install wmctrl, xdotool, Chrome
- [ ] Sim 2: Configure F1 game (UDP: 172.18.159.209:20778)
- [ ] Sim 2: Set up browser autostart
- [ ] Sim 2: Reboot and verify
- [ ] Host: Set up SSH keys (optional)
- [ ] Host: Configure Stream Deck (optional)
- [ ] Test complete flow

### Daily Startup

- [ ] Turn on all 3 PCs
- [ ] Sim 1: F1 game auto-starts + Chrome auto-starts
- [ ] Sim 2: F1 game auto-starts + Chrome auto-starts
- [ ] Host: Run `./scripts/start_mac.sh`
- [ ] Verify all attract screens visible
- [ ] Test one QR code scan
- [ ] Ready for participants!

### Daily Shutdown

- [ ] Host: Run `./scripts/stop_mac.sh`
- [ ] Sim 1: Close F1 game
- [ ] Sim 2: Close F1 game
- [ ] Turn off all PCs

---

## Support

If you encounter issues, check:
1. Logs: `tail -f logs/*.log`
2. Network: `ping <ip-address>`
3. Services: `ps aux | grep python`
4. This documentation: [docs/](../docs/)

For Stream Deck specific help, see: [STREAM_DECK_CONTROL.md](STREAM_DECK_CONTROL.md)

For deployment details, see: [DEPLOYMENT.md](DEPLOYMENT.md)
