# F1 Window Controller - Chrome Extension

Automatically switches between browser and F1 game on simulator PCs.

## 🎯 What It Does

- Listens for race start/end events from your web app
- Automatically switches windows (Alt+Tab) without player interaction
- Works on Windows, Linux, and macOS
- **Zero player interaction required**

---

## 📦 Installation (One-Time Per Sim PC)

### Step 1: Install Native Host

The native host is a Python script that actually performs the window switching.

**On Linux (Ubuntu/Debian):**
```bash
# Install dependencies
sudo apt install -y wmctrl xdotool python3

# Copy native host
sudo cp native-host.py /usr/local/bin/f1-window-switcher
sudo chmod +x /usr/local/bin/f1-window-switcher

# Create native messaging manifest
mkdir -p ~/.config/google-chrome/NativeMessagingHosts/
cat > ~/.config/google-chrome/NativeMessagingHosts/com.f1.windowswitcher.json << 'EOF'
{
  "name": "com.f1.windowswitcher",
  "description": "F1 Window Switcher for Simulators",
  "path": "/usr/local/bin/f1-window-switcher",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://EXTENSION_ID_WILL_BE_FILLED/"
  ]
}
EOF
```

**On Windows:**
```powershell
# Copy native-host.py to C:\Program Files\F1WindowSwitcher\
New-Item -Path "C:\Program Files\F1WindowSwitcher" -ItemType Directory -Force
Copy-Item native-host.py "C:\Program Files\F1WindowSwitcher\f1-window-switcher.py"

# Create native messaging manifest
$manifestPath = "$env:LOCALAPPDATA\Google\Chrome\User Data\NativeMessagingHosts"
New-Item -Path $manifestPath -ItemType Directory -Force

@"
{
  "name": "com.f1.windowswitcher",
  "description": "F1 Window Switcher for Simulators",
  "path": "C:\\Program Files\\F1WindowSwitcher\\f1-window-switcher.py",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://EXTENSION_ID_WILL_BE_FILLED/"
  ]
}
"@ | Out-File -FilePath "$manifestPath\com.f1.windowswitcher.json" -Encoding UTF8
```

### Step 2: Install Chrome Extension

1. Open Chrome
2. Go to `chrome://extensions/`
3. Enable "Developer mode" (toggle in top-right)
4. Click "Load unpacked"
5. Select the `chrome-extension` folder
6. **Copy the Extension ID** (something like `abcdefgh...`)

### Step 3: Update Native Host Manifest

Replace `EXTENSION_ID_WILL_BE_FILLED` with your actual extension ID:

**Linux:**
```bash
# Replace EXTENSION_ID_WILL_BE_FILLED with your actual ID
nano ~/.config/google-chrome/NativeMessagingHosts/com.f1.windowswitcher.json
```

**Windows:**
```powershell
notepad "$env:LOCALAPPDATA\Google\Chrome\User Data\NativeMessagingHosts\com.f1.windowswitcher.json"
```

### Step 4: Test

Open Chrome console (F12) on your simulator page and type:
```javascript
F1Controller.switchToGame()
```

The window should switch to the F1 game!

---

## 🎮 Usage in Your Web App

### Option 1: Custom Events (Recommended)

```javascript
// In your attract screen / dashboard page

// Switch to game when race starts
function startRace() {
  window.dispatchEvent(new CustomEvent('f1:switchToGame'));
}

// Switch back to browser when race ends
function endRace() {
  window.dispatchEvent(new CustomEvent('f1:switchToBrowser'));
}

// Listen for success/failure
window.addEventListener('message', (event) => {
  if (event.data.type === 'F1_SWITCHED_TO_GAME') {
    console.log('✓ Switched to game');
  }

  if (event.data.type === 'F1_SWITCH_FAILED') {
    console.error('✗ Switch failed:', event.data.error);
  }
});
```

### Option 2: PostMessage

```javascript
// Switch to game
window.postMessage({ type: 'F1_SWITCH_TO_GAME' }, '*');

// Switch to browser
window.postMessage({ type: 'F1_SWITCH_TO_BROWSER' }, '*');
```

### Option 3: Direct API (for testing)

```javascript
// Available in console
F1Controller.switchToGame();
F1Controller.switchToBrowser();
F1Controller.test();  // Shows available commands
```

---

## 🔧 Integration with Flask App

Update your Stream Deck control endpoints to trigger events:

```python
# In src/app.py

@app.route('/api/control/start-race', methods=['POST'])
def control_start_race():
    """Stream Deck START - triggers window switch via browser extension"""
    # No need for SSH commands anymore!
    # The browser extension will handle window switching

    # Just broadcast to connected browsers
    socketio.emit('raceStarting', {
        'rigs': [1, 2],
        'timestamp': datetime.now().isoformat()
    })

    return jsonify({
        "success": True,
        "message": "Race start signal sent - extension will switch windows"
    })
```

Update your attract screen template:

```javascript
// In templates/attract_screen_single.html

socket.on('raceStarting', (data) => {
  if (data.rigs.includes(rigNumber)) {
    // Trigger extension to switch windows
    window.dispatchEvent(new CustomEvent('f1:switchToGame'));

    // Show overlay for visual feedback
    showGameStartOverlay();
  }
});
```

---

## 📋 Troubleshooting

### Extension not working?

1. **Check extension is loaded:**
   - Go to `chrome://extensions/`
   - Ensure "F1 Window Controller" is enabled
   - Check for errors

2. **Check native host connection:**
   - Open console (F12)
   - Look for "✓ Extension is active and ready"
   - If you see "✗ Extension is not responding", native host isn't connected

3. **Check native host logs:**
   ```bash
   tail -f /tmp/f1-window-switcher.log
   ```

4. **Test manually:**
   ```javascript
   F1Controller.test()
   F1Controller.switchToGame()
   ```

### Window not switching?

1. **Linux:** Make sure wmctrl is installed
   ```bash
   which wmctrl
   which xdotool
   ```

2. **Windows:** Make sure Python is in PATH
   ```powershell
   python --version
   ```

3. **Check F1 game is running:**
   - Extension looks for window with "F1" in the title
   - Game must be running (can be minimized)

4. **Try Alt+Tab fallback:**
   - Even if game title doesn't match, extension will try Alt+Tab

---

## 🎨 Icons

You need 3 icon files. Create simple ones:

```bash
# Create placeholder icons (you can replace with nicer ones later)
convert -size 16x16 xc:blue chrome-extension/icon16.png
convert -size 48x48 xc:blue chrome-extension/icon48.png
convert -size 128x128 xc:blue chrome-extension/icon128.png
```

Or download F1 icons and rename them.

---

## 🚀 Deployment Checklist

- [ ] Install wmctrl/xdotool on Linux sims (or have Python on Windows)
- [ ] Copy native-host.py to /usr/local/bin/
- [ ] Create native messaging manifest
- [ ] Load extension in Chrome
- [ ] Copy extension ID
- [ ] Update manifest with extension ID
- [ ] Test with F1Controller.switchToGame()
- [ ] Verify logs: `tail -f /tmp/f1-window-switcher.log`
- [ ] Update Flask app to remove SSH commands
- [ ] Update attract screen to dispatch events
- [ ] Test full flow: QR code → START button → Window switches

---

## ✅ Advantages

- ✅ **Fully automatic** - zero player interaction
- ✅ **Works on all OS** (Windows/Linux/Mac)
- ✅ **No SSH required** - perfect since SSH is timing out
- ✅ **Easy to debug** - logs, console messages
- ✅ **Lightweight** - small Python script
- ✅ **Reliable** - direct window control

---

## 📦 Files

- `manifest.json` - Extension configuration
- `background.js` - Background service worker
- `content.js` - Injected into web pages
- `native-host.py` - Python script that switches windows
- `README.md` - This file
- `icon16.png`, `icon48.png`, `icon128.png` - Extension icons

---

## 🔒 Security

- Extension only works on `http://172.18.159.209:8080/*`
- Native host only accepts commands from this extension
- No external network access
- Logs stored locally for debugging

---

**Questions? Check the logs:**
```bash
tail -f /tmp/f1-window-switcher.log
```
