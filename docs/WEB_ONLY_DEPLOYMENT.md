# Web-Only Deployment (No Software Installation)

## 🌐 Zero-Install Solution

This deployment requires **ZERO software installation** on the sim PCs. Everything runs in the browser.

---

## 🎯 Key Changes

### What We Remove:
- ❌ No SSH
- ❌ No wmctrl/xdotool
- ❌ No Python scripts on sims
- ❌ No autostart configuration

### What We Use Instead:
- ✅ Pure web application
- ✅ Manual window switching (Alt+Tab)
- ✅ On-screen instructions
- ✅ Optional: USB HID device for automation
- ✅ Heroku hosting (optional)

---

## 🖥️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    HEROKU CLOUD                         │
│              (or Local Mac as Server)                   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Flask App (Python)                              │  │
│  │  - Serves web pages                              │  │
│  │  - Receives UDP telemetry                        │  │
│  │  - Broadcasts via WebSockets                     │  │
│  │  - Stores sessions in PostgreSQL (Heroku)        │  │
│  │    or SQLite (Local)                             │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
                           │ HTTPS/WebSocket
                           ↓
┌─────────────────────────────────────────────────────────┐
│                    LOCAL NETWORK                         │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  Sim 1 PC   │  │  Sim 2 PC   │  │  Host PC    │    │
│  │             │  │             │  │  (Control)  │    │
│  │  Browser    │  │  Browser    │  │             │    │
│  │  Only       │  │  Only       │  │  Browser    │    │
│  │             │  │             │  │  + Stream   │    │
│  │  F1 Game    │  │  F1 Game    │  │    Deck     │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## 🎮 Window Switching Solutions

### Option 1: Manual Alt+Tab (Simplest)

**How it works:**
1. Sim screens show attract page with **giant overlay** when race starts
2. Overlay says: "Press Alt+Tab to switch to F1 game"
3. Participant presses Alt+Tab
4. Browser stays open in background
5. When race ends, participant presses Alt+Tab again to return

**Pros:**
- ✅ Zero setup
- ✅ Works on any OS
- ✅ No special hardware

**Cons:**
- ⚠️ Requires participant action
- ⚠️ Participants might forget

### Option 2: On-Screen Button (Better)

**How it works:**
1. Attract screen has a **big "Switch to Game" button**
2. When pressed, opens F1 game URL scheme (if supported)
3. Or displays instructions: "Press Alt+Tab now"
4. Browser can detect when window loses/gains focus
5. Can show reminder to switch back when done

**Implementation:**
```javascript
// Detect window focus changes
window.addEventListener('blur', () => {
  console.log('User switched to game');
});

window.addEventListener('focus', () => {
  console.log('User returned to browser');
});

// Show instructions
function showSwitchInstructions() {
  // Full-screen overlay with:
  // "Press Alt+Tab to switch to F1 game"
  // Big arrow pointing to keyboard
}
```

### Option 3: USB HID Device (Advanced)

**Hardware solution:**
- Small USB device (Arduino/Raspberry Pi Pico)
- Controlled via WebUSB API from browser
- Sends keyboard commands (Alt+Tab) when triggered
- ~$10-20 per device

**How it works:**
1. Plug USB device into each sim PC
2. Browser connects via WebUSB
3. When race starts, browser sends command to USB device
4. USB device simulates Alt+Tab keypress
5. Window switches automatically

---

## 🚀 Deployment Options

### Option A: Local Mac as Server (Easiest)

**Setup:**
1. Run Flask on your Mac (already done)
2. Sims access via local IP: `http://172.18.159.209:8080`
3. UDP receivers run on Mac
4. Everything stays on local network

**Pros:**
- ✅ Already working
- ✅ No cloud costs
- ✅ Low latency
- ✅ Works offline

**Cons:**
- ⚠️ Mac must be on and running
- ⚠️ QR codes only work on local network (unless port forwarding)

### Option B: Heroku Deployment (Cloud)

**Setup:**
1. Deploy Flask app to Heroku
2. Use Heroku PostgreSQL instead of SQLite
3. Sims access via HTTPS: `https://f1-simulator.herokuapp.com`
4. UDP receivers stay on Mac (forward to Heroku via HTTP)

**Pros:**
- ✅ Access from anywhere
- ✅ QR codes work globally
- ✅ Auto-scaling
- ✅ Free tier available

**Cons:**
- ⚠️ Slightly higher latency for telemetry
- ⚠️ Need to forward UDP → HTTP

---

## 📝 Revised User Flow (Web-Only)

### 1. Idle State
```
Sim 1 & 2: Browser showing attract screen
           F1 game minimized in background
Host:      Dashboard showing "Waiting for participants"
```

### 2. Registration
```
User scans QR code → Registration form → Submit
Sim screen shows: "✅ Registered! When operator says GO, press Alt+Tab"
```

### 3. Race Start (Operator presses START)
```
Sim screens show HUGE overlay:
  ┌────────────────────────────────────────┐
  │                                        │
  │        🏁 RACE STARTING! 🏁           │
  │                                        │
  │     Press Alt + Tab on keyboard       │
  │          to switch to game            │
  │                                        │
  │         ⌨️  Alt + Tab                 │
  │                                        │
  │   (This message will stay visible     │
  │    until you switch)                  │
  └────────────────────────────────────────┘

Participants press Alt+Tab
Browser detects focus loss
Overlay stays visible for 30 seconds then minimizes
```

### 4. Race Active
```
Participants racing in F1 game
Browser running in background (still connected)
Dashboard shows live telemetry
```

### 5. Race End (Operator presses STOP)
```
Browser shows notification (if possible)
OR participants manually Alt+Tab back
Results screen visible in browser
After 30 seconds, returns to attract screen
```

---

## 🎨 Updated Attract Screen Design

Add these features to attract screen:

### Visual Cues
```html
<div class="switch-instructions" id="switchOverlay" style="display:none;">
  <div class="giant-message">
    <h1>🏁 RACE STARTING! 🏁</h1>
    <p class="huge-text">Press Alt + Tab to switch to F1 game</p>
    <div class="keyboard-visual">
      <span class="key">Alt</span> + <span class="key">Tab</span>
    </div>
    <p class="countdown">Starting in <span id="countdown">5</span>...</p>
  </div>
</div>

<style>
.switch-instructions {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.95);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}

.giant-message {
  text-align: center;
  animation: pulse 1s infinite;
}

.huge-text {
  font-size: 72px;
  color: #ffd700;
  margin: 40px 0;
}

.keyboard-visual .key {
  display: inline-block;
  padding: 20px 40px;
  background: linear-gradient(145deg, #2a2a2a, #1a1a1a);
  border: 3px solid #ffd700;
  border-radius: 10px;
  font-size: 48px;
  font-weight: bold;
  margin: 0 10px;
  box-shadow: 0 8px 16px rgba(0,0,0,0.4);
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}
</style>

<script>
// Listen for race start event
eventSource.addEventListener('message', (event) => {
  const data = JSON.parse(event.data);

  if (data.raceStarting) {
    showSwitchOverlay();
  }

  if (data.raceEnded) {
    showReturnOverlay();
  }
});

function showSwitchOverlay() {
  document.getElementById('switchOverlay').style.display = 'flex';

  // Countdown
  let count = 5;
  const countdownEl = document.getElementById('countdown');
  const timer = setInterval(() => {
    count--;
    countdownEl.textContent = count;
    if (count === 0) {
      clearInterval(timer);
      countdownEl.parentElement.textContent = 'Switch now!';
    }
  }, 1000);

  // Detect when user switches away
  window.addEventListener('blur', function onBlur() {
    console.log('User switched to game!');
    // Minimize overlay after they switch
    setTimeout(() => {
      document.getElementById('switchOverlay').style.display = 'none';
    }, 2000);
    window.removeEventListener('blur', onBlur);
  });
}

function showReturnOverlay() {
  // Show "Race finished, press Alt+Tab to return" message
  // Similar to above but for return journey
}
</script>
```

---

## 🎛️ Host Control Panel

Instead of Stream Deck buttons triggering SSH, they trigger **WebSocket broadcasts**:

### Updated Control Flow

```javascript
// When host presses START button
fetch('/api/control/start-race', { method: 'POST' })
  .then(() => {
    // Flask broadcasts to all connected browsers:
    // { event: 'raceStarting', rigs: [1, 2] }
  });

// Sim browsers receive event
socket.on('raceStarting', (data) => {
  if (data.rigs.includes(myRigNumber)) {
    showSwitchOverlay();
  }
});
```

---

## 🔧 Implementation Changes

### 1. Remove SSH Commands from Control Endpoints

```python
# OLD (with SSH)
@app.route('/api/control/start-race', methods=['POST'])
def control_start_race():
    subprocess.Popen(["ssh", "sim1admin@192.168.8.22", "..."])
    ...

# NEW (web-only)
@app.route('/api/control/start-race', methods=['POST'])
def control_start_race():
    # Broadcast to all connected browsers
    socketio.emit('raceStarting', {
        'rigs': [1, 2],
        'timestamp': datetime.now().isoformat()
    })

    return jsonify({
        "success": True,
        "message": "Race start signal sent to browsers"
    })
```

### 2. Add WebSocket Support

```python
# Install flask-socketio
# Already in requirements.txt

from flask_socketio import SocketIO, emit

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    logger.info('Browser connected')

@socketio.on('rig_ready')
def handle_rig_ready(data):
    logger.info(f"Rig {data['rig']} is ready")
    emit('ack', {'status': 'ready'})
```

### 3. Update Frontend

```javascript
// Connect to WebSocket
const socket = io('http://172.18.159.209:8080');

socket.on('raceStarting', (data) => {
  showSwitchOverlay();
});

socket.on('raceEnded', (data) => {
  showReturnOverlay();
});

socket.on('systemRestart', (data) => {
  window.location.reload();
});
```

---

## 📦 Heroku Deployment (Optional)

### Procfile
```
web: gunicorn src.app:app --bind 0.0.0.0:$PORT --worker-class eventlet -w 1
```

### runtime.txt
```
python-3.11.6
```

### Deploy Steps
```bash
# Install Heroku CLI
brew install heroku

# Login
heroku login

# Create app
heroku create f1-simulator

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Deploy
git push heroku master

# View logs
heroku logs --tail
```

---

## 🎯 Simplified Setup (Web-Only)

### On Sim PCs (ONE TIME ONLY):

1. **Open browser to attract screen**:
   - Sim 1: `http://172.18.159.209:8080/attract?rig=1`
   - Sim 2: `http://172.18.159.209:8080/attract?rig=2`

2. **Press F11 for fullscreen** (optional)

3. **Keep F1 game running in background**

4. **That's it!** No software to install.

### On Host PC:

Same as before - run `./scripts/start_mac.sh`

### During Race:

1. Participants scan QR code
2. Operator presses START on Stream Deck (or clicks button)
3. **Sim screens show giant "Press Alt+Tab" message**
4. Participants press Alt+Tab to switch to game
5. They race
6. Operator presses STOP
7. **Screens show "Press Alt+Tab to see results"**
8. Participants press Alt+Tab back to browser
9. Results displayed
10. Auto-returns to attract screen

---

## 🤔 Alternative: Voice Commands

If you want even more automation:

```javascript
// Use Web Speech API
const recognition = new webkitSpeechRecognition();
recognition.onresult = (event) => {
  const command = event.results[0][0].transcript.toLowerCase();

  if (command.includes('start race')) {
    showSwitchOverlay();
  }
  if (command.includes('end race')) {
    showReturnOverlay();
  }
};

recognition.start();
```

Operator can say "Start race!" and all screens react.

---

## ✅ Advantages of Web-Only Approach

1. ✅ **Zero installation** on sim PCs
2. ✅ **Cross-platform** (Windows/Linux/Mac)
3. ✅ **Easy updates** (just refresh browser)
4. ✅ **No SSH/firewall issues**
5. ✅ **Works with Heroku**
6. ✅ **Simpler troubleshooting**
7. ✅ **Mobile-friendly** control panel

## ⚠️ Tradeoff

- Participants must press Alt+Tab (not fully automatic)
- But this is **very simple** and **always works**
- Can add visual/audio cues to make it obvious

---

## 🎬 Summary

**Old way:**
- SSH into sims
- Run wmctrl commands
- Automatic window switching

**New way:**
- Pure web browsers
- Giant on-screen instructions
- Participants press Alt+Tab (10 seconds max)
- **MUCH simpler deployment**

**Which do you prefer?** I can help implement either approach!

