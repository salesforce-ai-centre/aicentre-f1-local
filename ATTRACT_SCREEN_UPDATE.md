# Attract Screen Update - Single Rig Display

## What Changed

The attract screen now shows **only one QR code per simulator**, making it clear which rig the user is interacting with.

## Old Behavior
- `/attract` showed BOTH QR codes (Rig 1 and Rig 2)
- Confusing for users - which QR code should they scan?

## New Behavior
- `/attract?rig=1` shows **ONLY Simulator 1** QR code (Left rig)
- `/attract?rig=2` shows **ONLY Simulator 2** QR code (Right rig)
- Larger QR code, clearer display
- Shows "SIMULATOR 1 - LEFT" or "SIMULATOR 2 - RIGHT" prominently

## Usage

### For Simulator 1 (Left Rig)
Open this URL on the left simulator's display:
```
http://localhost:8080/attract?rig=1
```

### For Simulator 2 (Right Rig)
Open this URL on the right simulator's display:
```
http://localhost:8080/attract?rig=2
```

### Setup Instructions

1. **On Left Rig Display**:
   - Open browser to `http://localhost:8080/attract?rig=1`
   - Press F11 for fullscreen
   - Shows red-themed "SIMULATOR 1 - LEFT" with QR code

2. **On Right Rig Display**:
   - Open browser to `http://localhost:8080/attract?rig=2`
   - Press F11 for fullscreen
   - Shows cyan-themed "SIMULATOR 2 - RIGHT" with QR code

3. **Bookmark These URLs** on each rig for easy access

## Visual Differences

### Simulator 1 (Left)
- **Border Color**: Red (#ff6b6b)
- **Title**: "🏁 SIMULATOR 1 - LEFT"
- **QR Code**: Links to `/start?rig=1`

### Simulator 2 (Right)
- **Border Color**: Cyan (#4ecdc4)
- **Title**: "🏁 SIMULATOR 2 - RIGHT"
- **QR Code**: Links to `/start?rig=2`

## Error Handling

If you visit `/attract` without the `?rig=` parameter, you'll see a helpful error page:

```
⚠️ Missing Rig Parameter

Please specify which simulator this is:
[Simulator 1 (Left)]  [Simulator 2 (Right)]
```

Click one of the buttons to go to the correct attract screen.

## Leaderboard Display

Each simulator shows the same leaderboard data:
- **Today**: Today's best laps across both rigs
- **Month**: This month's best laps
- **Track**: All-time records for current track

## Technical Details

**New Template**: `templates/attract_screen_single.html`
- Single QR code display
- Rig-specific styling
- Larger, more prominent QR code (300x300px vs 256x256px)

**Updated Route**: `src/app.py`
```python
@app.route('/attract')
def attract_screen():
    rig = request.args.get('rig', type=int)
    if not rig or rig not in [1, 2]:
        return error_page
    return render_template('attract_screen_single.html')
```

**Old Template** (deprecated): `templates/attract_screen.html`
- Still exists but not used
- Can be deleted or kept as reference

## Browser Bookmarks (Recommended)

Save these bookmarks on each rig:

**Left Rig**:
- Name: "F1 Sim 1 Attract"
- URL: `http://localhost:8080/attract?rig=1`

**Right Rig**:
- Name: "F1 Sim 2 Attract"
- URL: `http://localhost:8080/attract?rig=2`

## Auto-Start on Boot (Optional)

To auto-open the attract screen when each rig boots:

**macOS**:
```bash
# Add to Login Items in System Preferences
# Command: open -a "Google Chrome" --args --kiosk http://localhost:8080/attract?rig=1
```

**Linux**:
```bash
# Add to .xinitrc or autostart
chromium-browser --kiosk http://localhost:8080/attract?rig=1
```

**Windows**:
```batch
REM Create startup shortcut
REM Target: "C:\Program Files\Google\Chrome\Application\chrome.exe" --kiosk http://localhost:8080/attract?rig=1
```

## Testing

1. **Test Simulator 1**:
   ```
   http://localhost:8080/attract?rig=1
   ```
   - Should show red border
   - Title says "SIMULATOR 1 - LEFT"
   - QR code generates successfully

2. **Test Simulator 2**:
   ```
   http://localhost:8080/attract?rig=2
   ```
   - Should show cyan border
   - Title says "SIMULATOR 2 - RIGHT"
   - QR code generates successfully

3. **Test Error Handling**:
   ```
   http://localhost:8080/attract
   ```
   - Should show error page with selection buttons

4. **Scan QR Code**:
   - Scan QR from Sim 1
   - Should land on `/start?rig=1`
   - Form should show "Rig 1 - Left" badge

## Summary

✅ **Fixed**: Each simulator now shows only its own QR code
✅ **Clearer**: Large, prominent display with rig identification
✅ **User-friendly**: No confusion about which QR to scan
✅ **Themed**: Color-coded for easy visual identification

**URLs to remember**:
- Sim 1: `http://localhost:8080/attract?rig=1`
- Sim 2: `http://localhost:8080/attract?rig=2`
