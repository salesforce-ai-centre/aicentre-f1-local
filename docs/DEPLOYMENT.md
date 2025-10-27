# F1 Simulator System - Deployment Guide

## System Overview

This F1 telemetry system runs on a **3-PC local network** with internet access for mobile users.

### Hardware Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        INTERNET                              │
│                 (Mobile Users via QR Code)                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    Port Forwarding
                     (Router/Firewall)
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                    LOCAL NETWORK                             │
│              (192.168.8.x / 172.18.x)                        │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   PC 1       │  │   PC 2       │  │   PC 3       │      │
│  │ Simulator 1  │  │ Simulator 2  │  │  Controller  │      │
│  │ (Left Rig)   │  │ (Right Rig)  │  │   (MacBook)  │      │
│  │              │  │              │  │              │      │
│  │ 192.168.8.22 │  │ 192.168.8.21 │  │172.18.159.209│      │
│  │              │  │              │  │              │      │
│  │ - F1 Game    │  │ - F1 Game    │  │ - Flask App  │      │
│  │ - UDP:20777  │  │ - UDP:20778  │  │ - HTTP:8080  │      │
│  │ - Browser    │  │ - Browser    │  │ - SQLite DB  │      │
│  │   /attract   │  │   /attract   │  │ - Receivers  │      │
│  │   ?rig=1     │  │   ?rig=2     │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │             Overhead Display (Optional)              │   │
│  │                 Shows: /dual                         │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

## IP Address Plan

| Device | IP Address | Role | Services | Username |
|--------|-----------|------|----------|----------|
| **PC 1 (Sim 1)** | `192.168.8.22` | Simulator 1 (Left) | F1 Game (UDP 20777), Browser (/attract?rig=1) | `sim1admin` |
| **PC 2 (Sim 2)** | `192.168.8.21` | Simulator 2 (Right) | F1 Game (UDP 20778), Browser (/attract?rig=2) | `sim2admin` |
| **PC 3 (Controller)** | `172.18.159.209` | Controller/Host (MacBook) | Flask (8080), Receivers, Database | `jacob.berry` |
| **Router** | `192.168.8.1` or `172.18.159.1` | Gateway | Port forwarding 80→8080 |

**Note:** PC 3 is on a different subnet but can communicate with sims through the router.

## Installation Instructions

### PC 3 (Controller/Host) - Main Server

This PC runs the Flask application, both UDP receivers, and the database.

#### 1. Initial Setup

```bash
# Clone the repository
cd /opt
sudo git clone <your-repo-url> f1-simulator
cd /opt/f1-simulator

# Install system dependencies (Ubuntu/Debian)
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r config/requirements.txt
```

#### 2. Configure Environment

```bash
# Copy environment template
cp config/.env.example config/.env

# Edit configuration
nano config/.env
```

Set the following in `config/.env`:

```bash
# Server Configuration
FLASK_HOST=0.0.0.0  # Listen on all interfaces
FLASK_PORT=8080

# Database
DATABASE_PATH=/opt/f1-simulator/data/sessions.db

# Data Cloud (Optional - for Salesforce integration)
DATACLOUD_ENABLED=false

# For production with HTTPS
# FLASK_ENV=production
```

#### 3. Create Systemd Services

Create three systemd service files for automatic startup:

**a) Flask Web Server**

```bash
sudo nano /etc/systemd/system/f1-flask.service
```

```ini
[Unit]
Description=F1 Telemetry Flask Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/f1-simulator
Environment="PATH=/opt/f1-simulator/venv/bin"
ExecStart=/opt/f1-simulator/venv/bin/python3 src/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**b) UDP Receiver - Rig 1**

```bash
sudo nano /etc/systemd/system/f1-receiver-rig1.service
```

```ini
[Unit]
Description=F1 Telemetry Receiver - Rig 1
After=network.target f1-flask.service
Requires=f1-flask.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/f1-simulator
Environment="PATH=/opt/f1-simulator/venv/bin"
ExecStart=/opt/f1-simulator/venv/bin/python3 src/receiver.py --url http://localhost:8080/data --driver "Rig 1" --port 20777 --rig 1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**c) UDP Receiver - Rig 2**

```bash
sudo nano /etc/systemd/system/f1-receiver-rig2.service
```

```ini
[Unit]
Description=F1 Telemetry Receiver - Rig 2
After=network.target f1-flask.service
Requires=f1-flask.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/f1-simulator
Environment="PATH=/opt/f1-simulator/venv/bin"
ExecStart=/opt/f1-simulator/venv/bin/python3 src/receiver.py --url http://localhost:8080/data --driver "Rig 2" --port 20778 --rig 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**NOTE:** Rig 2 uses port **20778** because each receiver needs a unique UDP port.

#### 4. Enable and Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services (auto-start on boot)
sudo systemctl enable f1-flask.service
sudo systemctl enable f1-receiver-rig1.service
sudo systemctl enable f1-receiver-rig2.service

# Start services
sudo systemctl start f1-flask.service
sudo systemctl start f1-receiver-rig1.service
sudo systemctl start f1-receiver-rig2.service

# Check status
sudo systemctl status f1-flask.service
sudo systemctl status f1-receiver-rig1.service
sudo systemctl status f1-receiver-rig2.service
```

#### 5. View Logs

```bash
# Flask logs
sudo journalctl -u f1-flask.service -f

# Receiver logs
sudo journalctl -u f1-receiver-rig1.service -f
sudo journalctl -u f1-receiver-rig2.service -f
```

### PC 1 & PC 2 (Simulators) - Display Only

These PCs run the F1 game and display the attract screen in a browser.

#### 1. Configure F1 Game

**F1 25 / F1 24 Game Settings:**

1. Go to **Settings → Telemetry Settings**
2. Set **UDP Telemetry**: ON
3. Set **UDP Port**:
   - **PC 1 (Rig 1)**: `20777`
   - **PC 2 (Rig 2)**: `20778`
4. Set **UDP IP Address**: `172.18.159.209` (PC 3's IP)
5. Set **UDP Format**: F1 2025 (or F1 2024 depending on game)
6. Set **UDP Broadcast Mode**: ON

#### 2. Configure Browser Kiosk Mode

**On PC 1 (Rig 1):**

```bash
# Install Chromium (if not already installed)
sudo apt install -y chromium-browser unclutter

# Create autostart script
mkdir -p ~/.config/autostart
nano ~/.config/autostart/f1-display.desktop
```

```ini
[Desktop Entry]
Type=Application
Name=F1 Attract Screen - Rig 1
Exec=/usr/bin/chromium-browser --kiosk --incognito --disable-infobars --noerrdialogs http://172.18.159.209:8080/attract?rig=1
Terminal=false
```

**On PC 2 (Rig 2):**

Same as above, but change the URL to:
```
http://172.18.159.209:8080/attract?rig=2
```

#### 3. Hide Mouse Cursor (Optional)

```bash
# Install unclutter
sudo apt install -y unclutter

# Add to autostart
nano ~/.config/autostart/hide-cursor.desktop
```

```ini
[Desktop Entry]
Type=Application
Name=Hide Mouse Cursor
Exec=/usr/bin/unclutter -idle 0.1
Terminal=false
```

## Network Configuration

### Fixed IP Addresses

Configure static IPs on all 3 PCs to prevent DHCP changes.

**Example for Ubuntu/Debian (netplan):**

```bash
sudo nano /etc/netplan/01-netcfg.yaml
```

**PC 1 (192.168.1.10):**
```yaml
network:
  version: 2
  ethernets:
    eth0:  # or your interface name (check with: ip link)
      dhcp4: no
      addresses:
        - 192.168.1.10/24
      gateway4: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
```

**PC 2 (192.168.1.11):**
```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: no
      addresses:
        - 192.168.1.11/24
      gateway4: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
```

**PC 3 (192.168.1.12):**
```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: no
      addresses:
        - 192.168.1.12/24
      gateway4: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
```

Apply changes:
```bash
sudo netplan apply
```

### Firewall Configuration (PC 3)

```bash
# Allow HTTP traffic
sudo ufw allow 8080/tcp

# Allow UDP from simulators (optional - for security)
sudo ufw allow from 192.168.8.22 to any port 20777 proto udp
sudo ufw allow from 192.168.8.21 to any port 20778 proto udp

# Enable firewall
sudo ufw enable
```

## Internet Access for Mobile Users

Mobile users scanning QR codes need to access the system from the internet.

### Option 1: Port Forwarding (Simplest)

Configure your router to forward external HTTP traffic to PC 3:

1. Log into your router (typically http://192.168.1.1)
2. Find **Port Forwarding** or **Virtual Server** settings
3. Add rule:
   - **External Port**: 80 (HTTP)
   - **Internal IP**: 172.18.159.209
   - **Internal Port**: 8080
   - **Protocol**: TCP

4. Find your **public IP address**: https://whatismyipaddress.com/

5. **Update QR codes** in attract screens to use your public IP:

Edit `templates/attract_screen_single.html` and find:
```javascript
const qrUrl = `http://localhost:8080/start?rig=${rigNumber}`;
```

Replace with your public IP:
```javascript
const qrUrl = `http://YOUR_PUBLIC_IP/start?rig=${rigNumber}`;
```

**Security Warning:** This exposes your system to the internet. Use HTTPS and authentication in production.

### Option 2: Dynamic DNS (For Changing Public IPs)

If your ISP changes your public IP frequently:

1. Sign up for a free DDNS service (e.g., No-IP, DuckDNS, Dynu)
2. Create a hostname (e.g., `f1-simulator.ddns.net`)
3. Install DDNS client on PC 3 to keep IP updated
4. Use the hostname in QR codes

**Example with No-IP:**
```bash
# Install No-IP client on PC 3
cd /tmp
wget http://www.noip.com/client/linux/noip-duc-linux.tar.gz
tar xzf noip-duc-linux.tar.gz
cd noip-*
sudo make install
sudo /usr/local/bin/noip2 -C  # Configure
sudo /usr/local/bin/noip2     # Start
```

QR code URL becomes: `http://f1-simulator.ddns.net/start?rig=1`

### Option 3: Cloudflare Tunnel (Most Secure - Recommended)

Use Cloudflare Tunnel for secure HTTPS access without port forwarding:

1. Sign up for Cloudflare (free tier)
2. Install cloudflared on PC 3:

```bash
# Download cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Authenticate
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create f1-simulator

# Configure tunnel
nano ~/.cloudflared/config.yml
```

```yaml
tunnel: f1-simulator
credentials-file: /home/USER/.cloudflared/TUNNEL-ID.json

ingress:
  - hostname: f1-simulator.yourdomain.com
    service: http://localhost:8080
  - service: http_status:404
```

```bash
# Run tunnel
cloudflared tunnel run f1-simulator

# Or install as service
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

QR code URL becomes: `https://f1-simulator.yourdomain.com/start?rig=1`

**Benefits:**
- Automatic HTTPS
- No port forwarding needed
- DDoS protection
- Works behind NAT/firewall

## URL Reference

| Screen | URL | Device | Description |
|--------|-----|--------|-------------|
| **Welcome** | `http://172.18.159.209:8080/` | Any | Admin panel with navigation |
| **Attract - Rig 1** | `http://172.18.159.209:8080/attract?rig=1` | PC 1 | QR code + leaderboards (Rig 1) |
| **Attract - Rig 2** | `http://172.18.159.209:8080/attract?rig=2` | PC 2 | QR code + leaderboards (Rig 2) |
| **Dual Dashboard** | `http://172.18.159.209:8080/dual` | Overhead | Both simulators side-by-side |
| **Registration Form** | `http://YOUR_PUBLIC_IP/start?rig=1` | Mobile | User scans QR code |
| **Thank You** | `http://YOUR_PUBLIC_IP/thank-you?sessionId=...` | Mobile | Post-registration success |
| **Single Dashboard** | `http://172.18.159.209:8080/dashboard` | Debug | Legacy single-rig dashboard |

## User Flow

### Mobile User (Scanning QR Code)

1. User scans QR code on **Sim 1** or **Sim 2**
2. Mobile browser opens: `http://YOUR_PUBLIC_IP/start?rig=X`
3. User fills in:
   - Nickname
   - Accept terms & conditions
   - Acknowledge safety rules
4. Clicks "Start Racing"
5. Redirected to: `http://YOUR_PUBLIC_IP/thank-you?sessionId=...`
6. Sees success message: "You're all set! Put your phone away"
7. User puts phone away and heads to simulator

### Simulator Screen Flow

1. **Idle State**: Shows `/attract?rig=X` with:
   - Large QR code
   - Current race from F1 calendar
   - Leaderboards (day/month/track)
   - Developer test button (for debugging)

2. **User Completes Form**: Attract screen polls `/api/session/active/{rig}` every 2 seconds

3. **Session Detected**:
   - Shows "🏁 GAME START!" overlay with driver name
   - After 3 seconds, redirects to `/dual`

4. **Race Active**: `/dual` dashboard shows:
   - Both rigs side-by-side
   - Live telemetry from both games
   - Speed, RPM, gear, tire temps, lap times, etc.

5. **Race Ends**:
   - Receiver detects "SEND" packet (session end)
   - Marks session as completed
   - Shows summary screen with stats
   - After 10 seconds, returns to `/attract?rig=X`

## Testing the Deployment

### 1. Test Local Network Access

From PC 1 or PC 2:
```bash
curl http://172.18.159.209:8080/
# Should return welcome HTML
```

### 2. Test Attract Screens

Open browser on PC 1: `http://172.18.159.209:8080/attract?rig=1`
Open browser on PC 2: `http://172.18.159.209:8080/attract?rig=2`

You should see:
- QR code
- Current F1 race from calendar
- Empty leaderboards (initially)

### 3. Test Registration Flow

On your mobile phone (connected to same WiFi):
1. Navigate to: `http://172.18.159.209:8080/start?rig=1`
2. Fill in form and submit
3. Should redirect to thank you page
4. Check that Sim 1 screen shows "GAME START!" overlay
5. After 3 seconds, should redirect to dual dashboard

### 4. Test UDP Telemetry

1. Start F1 game on PC 1
2. Start a race/session
3. Check receiver logs:
   ```bash
   sudo journalctl -u f1-receiver-rig1.service -f
   ```
4. Should see packets being received and decoded
5. Dashboard should update in real-time

### 5. Test Internet Access

From a mobile device **not** on your WiFi (use cellular data):
1. Navigate to: `http://YOUR_PUBLIC_IP/start?rig=1`
2. Complete the form
3. Should work exactly like local access

## Troubleshooting

### Services Not Starting

```bash
# Check service status
sudo systemctl status f1-flask.service
sudo systemctl status f1-receiver-rig1.service
sudo systemctl status f1-receiver-rig2.service

# View detailed logs
sudo journalctl -u f1-flask.service -n 50 --no-pager
```

### No Telemetry Data

1. **Check F1 game settings** - Ensure UDP is enabled and IP is correct
2. **Check receiver logs**:
   ```bash
   sudo journalctl -u f1-receiver-rig1.service -f
   ```
3. **Test UDP connection**:
   ```bash
   sudo tcpdump -i any udp port 20777
   ```
4. **Verify receiver is running**:
   ```bash
   sudo netstat -ulnp | grep 20777
   ```

### Mobile Users Can't Connect

1. **Check port forwarding** in router settings
2. **Test from external network** (use cellular data)
3. **Check firewall** on PC 3:
   ```bash
   sudo ufw status
   ```
4. **Verify public IP**: https://whatismyipaddress.com/

### Attract Screen Not Updating

1. **Check browser console** (F12) for JavaScript errors
2. **Test API endpoint**:
   ```bash
   curl http://172.18.159.209:8080/api/session/active/1
   ```
3. **Clear browser cache** and reload

### Database Issues

```bash
# Check database file
ls -lh /opt/f1-simulator/data/sessions.db

# Reset database (WARNING: deletes all data)
rm /opt/f1-simulator/data/sessions.db
sudo systemctl restart f1-flask.service
```

## Maintenance

### Updating the Application

```bash
cd /opt/f1-simulator
git pull
source venv/bin/activate
pip install -r config/requirements.txt
sudo systemctl restart f1-flask.service
sudo systemctl restart f1-receiver-rig1.service
sudo systemctl restart f1-receiver-rig2.service
```

### Backup Database

```bash
# Create backup
sudo cp /opt/f1-simulator/data/sessions.db /opt/f1-simulator/data/sessions.db.backup-$(date +%Y%m%d)

# Restore from backup
sudo cp /opt/f1-simulator/data/sessions.db.backup-20250101 /opt/f1-simulator/data/sessions.db
sudo systemctl restart f1-flask.service
```

### Monitor System Resources

```bash
# CPU and memory
htop

# Disk usage
df -h

# Service resource usage
systemctl status f1-flask.service
```

## Security Considerations

### For Production Deployment

1. **Use HTTPS** (Let's Encrypt + nginx reverse proxy)
2. **Add rate limiting** to prevent API abuse
3. **Implement CAPTCHA** on registration form
4. **Use environment-based secrets** (not .env in repo)
5. **Regular security updates**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
6. **Monitor logs** for suspicious activity
7. **Backup database regularly**

### Minimal nginx + Let's Encrypt Setup

```bash
# Install nginx and certbot
sudo apt install -y nginx certbot python3-certbot-nginx

# Configure nginx
sudo nano /etc/nginx/sites-available/f1-simulator
```

```nginx
server {
    listen 80;
    server_name f1-simulator.yourdomain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE support
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/f1-simulator /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d f1-simulator.yourdomain.com
```

## Quick Reference Commands

```bash
# Start all services
sudo systemctl start f1-flask f1-receiver-rig1 f1-receiver-rig2

# Stop all services
sudo systemctl stop f1-flask f1-receiver-rig1 f1-receiver-rig2

# Restart all services
sudo systemctl restart f1-flask f1-receiver-rig1 f1-receiver-rig2

# View all logs
sudo journalctl -u f1-flask -u f1-receiver-rig1 -u f1-receiver-rig2 -f

# Check if services are running
sudo systemctl is-active f1-flask f1-receiver-rig1 f1-receiver-rig2

# Reboot PC 3 (services auto-start)
sudo reboot
```

## Support

If you encounter issues:
1. Check logs first: `sudo journalctl -u f1-flask.service -f`
2. Verify network connectivity: `ping 172.18.159.209`
3. Test API endpoints: `curl http://172.18.159.209:8080/api/calendar/current`
4. Review this documentation
5. Check F1 game telemetry settings
