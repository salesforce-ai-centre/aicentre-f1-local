# Race Flow System Documentation

## Overview

The F1 Telemetry Dashboard now includes a complete race flow management system designed for a dual-rig racing simulator experience. The system handles the entire user journey from QR code scan to race completion, with leaderboards and session tracking.

## System Architecture

### Technology Stack
- **Backend**: Flask (Python) with Salesforce-style architecture patterns
- **Database**: SQLite (designed for easy migration to Salesforce)
- **Frontend**: Vanilla JavaScript with responsive HTML/CSS
- **Integration**: F1 UDP telemetry + session management

### Core Components

1. **Data Models** (`src/models/`)
   - `Session` - Salesforce-style custom object (Session__c)
   - `LapRecord` - Child object with Master-Detail relationship

2. **Repository Layer** (`src/repositories/`)
   - `Database` - SQLite connection manager
   - `SessionRepository` - SOQL-like query patterns

3. **Service Layer** (`src/services/`)
   - `SessionService` - Business logic for session lifecycle
   - `CalendarService` - F1 race calendar management

4. **API Endpoints** (`src/app.py`)
   - Salesforce REST API patterns
   - Session CRUD operations
   - Leaderboard queries

## User Flow

### 1. Attract Screen (Holding Screen)
**URL**: `/attract`

Displays when no one is racing:
- Large QR codes for both rigs (Left & Right)
- Current F1 race from calendar
- Rotating leaderboards:
  - Today's Best Laps
  - This Month's Best
  - Track Records
- Auto-refreshes every 30 seconds

### 2. QR Code Scan → Landing Page
**URL**: `/start?rig=1` or `/start?rig=2`

When user scans QR code:
- Shows current race/track info from F1 calendar
- Nickname input field
- Safety rules display
- Terms & conditions checkbox
- Safety rules acceptance checkbox
- Creates session in "Waiting" status

### 3. Race Dashboard
**URL**: `/?sessionId={id}&rig={rigNumber}`

Active racing screen:
- Real-time telemetry visualization
- Live timing and lap data
- Session automatically starts when F1 game begins
- System listens for "SEND" event to detect race end

### 4. Race Summary
**URL**: `/summary/{sessionId}`

Post-race statistics:
- Best lap time (highlighted)
- Total laps completed
- Top speed achieved
- Session duration
- Best sector times
- 10-second countdown before returning to attract screen

### 5. Back to Attract Screen
Auto-redirects to `/attract` showing updated leaderboards

## Session Lifecycle

### Session States (Salesforce pattern)
```
Waiting → Active → Completed
```

**Waiting**:
- Session created from QR landing page
- Driver info captured
- Race context populated from calendar

**Active**:
- Triggered when telemetry starts flowing
- UDP Session UID tracked
- Continuous telemetry updates

**Completed**:
- Triggered by F1 "SEND" event (session end)
- Final statistics calculated
- Available for leaderboards

## API Endpoints

### Session Management

#### Create Session
```http
POST /api/session
Content-Type: application/json

{
  "rigNumber": 1,
  "driverName": "Hamilton",
  "termsAccepted": true,
  "safetyAccepted": true
}
```

**Response**:
```json
{
  "success": true,
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "sessionName": "SES-20251023-RIG1-0001",
  "rigNumber": 1,
  "trackName": "Monaco",
  "raceName": "Monaco Grand Prix"
}
```

#### Start Session
```http
POST /api/session/{sessionId}/start
```

#### Complete Session
```http
POST /api/session/{sessionId}/complete
```

**Response** includes full session summary.

#### Get Session
```http
GET /api/session/{sessionId}
```

#### Get Active Session for Rig
```http
GET /api/session/active/{rigNumber}
```

### Leaderboards

#### Daily Leaderboard
```http
GET /api/leaderboard/daily?limit=10
GET /api/leaderboard/daily?track=Monaco&limit=10
```

#### Monthly Leaderboard
```http
GET /api/leaderboard/monthly?limit=10
```

#### Track Records
```http
GET /api/leaderboard/track?track=Monaco&limit=10
```

### Calendar

#### Get Current Race
```http
GET /api/calendar/current
```

**Response**:
```json
{
  "success": true,
  "calendar": {
    "loaded": true,
    "season": 2026,
    "totalRaces": 24,
    "currentRace": {
      "round": 8,
      "raceName": "Monaco Grand Prix",
      "country": "Monaco",
      "location": "Monaco",
      "circuit": "Circuit de Monaco",
      "startDate": "2026-06-05",
      "endDate": "2026-06-07",
      "hasSprint": false
    },
    "nextRaces": [...]
  }
}
```

## Database Schema

### Session__c Table

| Field | Type | Description |
|-------|------|-------------|
| Id | TEXT | UUID primary key |
| Name | TEXT | Auto-generated (SES-YYYYMMDD-RIGN-NNNN) |
| Rig_Number__c | INTEGER | 1 (Left) or 2 (Right) |
| Driver_Name__c | TEXT | Driver nickname |
| Track_Name__c | TEXT | Track location |
| Circuit_Name__c | TEXT | Full circuit name |
| Session_Status__c | TEXT | Waiting/Active/Completed |
| Race_Round__c | INTEGER | F1 calendar round number |
| Race_Name__c | TEXT | GP name (e.g., "Monaco Grand Prix") |
| Session_Start_Time__c | TEXT | ISO timestamp |
| Session_End_Time__c | TEXT | ISO timestamp |
| Best_Lap_Time__c | REAL | Milliseconds |
| Best_Sector_1/2/3_Time__c | REAL | Milliseconds |
| Total_Laps__c | INTEGER | Laps completed |
| Top_Speed__c | REAL | km/h |
| Terms_Accepted__c | INTEGER | Boolean (0/1) |

### Lap_Record__c Table

| Field | Type | Description |
|-------|------|-------------|
| Id | TEXT | UUID primary key |
| Session__c | TEXT | Foreign key to Session |
| Lap_Number__c | INTEGER | Lap number |
| Lap_Time__c | REAL | Total lap time (ms) |
| Sector_1/2/3_Time__c | REAL | Sector times (ms) |
| Is_Best_Lap__c | INTEGER | Boolean |
| Max_Speed__c | REAL | km/h |

## F1 Calendar Integration

### Calendar Files
- `F1-25-Calendar.json` - F1 2025 season
- `F1-26-Calendar.json` - F1 2026 season

### Auto-Selection Logic
1. Checks current date
2. Finds next upcoming race (or current race weekend)
3. Populates session with race context:
   - Race name
   - Track/circuit name
   - Round number
   - Country

### Calendar Service Features
- Auto-detects which calendar to use (based on date)
- Provides current race
- Lists next 3 upcoming races
- Track-based race lookup
- Formatted display strings

## UDP Event Integration

### Session End Detection

The system listens for the F1 UDP "SEND" event:

```python
# In receiver.py - Event packet processing
if event_code == 'SEND':
    # Session ended event detected
    payload['event'] = {
        'eventCode': 'SEND',
        'message': 'Session Ended'
    }
```

When `/data` endpoint receives SEND event:
```python
if session_event_code == 'SEND' and session_id:
    session_service.complete_session(session_id)
    # Triggers redirect to summary page
```

### Telemetry Updates

During active session:
```python
# Continuous updates to session
session_service.update_session_telemetry(session_id, {
    'lapNumber': current_lap,
    'currentLapTime': lap_time_ms,
    'sector1Time': s1_time,
    'speed': current_speed,
    ...
})
```

Tracks:
- Best lap time
- Best sector times
- Total laps
- Top speed

## QR Code Generation

### QR Code URLs
- **Rig 1 (Left)**: `http://localhost:8080/start?rig=1`
- **Rig 2 (Right)**: `http://localhost:8080/start?rig=2`

### Implementation
Uses `qrcodejs` library:
```javascript
new QRCode(element, {
    text: url,
    width: 256,
    height: 256
});
```

## Leaderboard Logic

### Ranking Criteria
All leaderboards ranked by **fastest lap time** (ascending):
```sql
ORDER BY Best_Lap_Time__c ASC
```

### Daily Leaderboard
- Sessions completed TODAY
- Filtered by date
- Optional track filter

### Monthly Leaderboard
- Sessions from current calendar month
- Filtered by month start date

### Track Records
- All-time best laps for specific track
- Requires track name parameter

## Automatic Screen Transitions

### Flow Control
1. **Attract → Start**: User scans QR code
2. **Start → Dashboard**: Form submission creates session
3. **Dashboard → Summary**: SEND event triggers completion
4. **Summary → Attract**: 10-second countdown auto-redirect

### JavaScript Redirect Examples

**From Summary to Attract**:
```javascript
setTimeout(() => {
    window.location.href = '/attract';
}, 10000); // 10 seconds
```

**From Start to Dashboard**:
```javascript
// After successful session creation
window.location.href = `/?sessionId=${sessionId}&rig=${rigNumber}`;
```

## Salesforce Migration Path

### Current SQLite → Future Salesforce

The system is designed using Salesforce patterns:

**Field Naming**:
- Custom fields use `__c` suffix
- Standard fields: `Id`, `Name`, `CreatedDate`

**Relationships**:
- Master-Detail: `Lap_Record__c.Session__c`
- Cascade delete on parent

**Query Patterns**:
```python
# Current SQLite
session_repo.query(where="Rig_Number__c = ?", params=(1,))

# Future Salesforce SOQL
query = "SELECT Id, Name FROM Session__c WHERE Rig_Number__c = 1"
```

**Repository Methods** mirror Salesforce Database class:
- `insert()` → `Database.insert()`
- `update()` → `Database.update()`
- `query()` → `SOQL queries`

### Migration Steps (Future)
1. Export SQLite data to CSV
2. Create custom objects in Salesforce
3. Use Data Import Wizard or Bulk API
4. Update repository layer to use Salesforce APIs
5. Data models remain unchanged (same field names)

## Configuration

### Database Location
```python
# Default: data/f1_telemetry.db
db = get_database("data/f1_telemetry.db")
```

### Calendar Year
```python
# Auto-detect or force specific year
calendar_service = CalendarService(calendar_year=2026)
```

## Testing

### Manual Testing Flow
1. Start Flask server: `python3 src/app.py`
2. Open `/attract` in browser
3. Scan QR code (or navigate to `/start?rig=1`)
4. Fill in driver name and accept terms
5. Click "Start Racing Session"
6. Start F1 game and begin session
7. Complete race (or trigger SEND event)
8. View summary screen
9. Auto-redirect to attract screen

### API Testing with curl

**Create Session**:
```bash
curl -X POST http://localhost:8080/api/session \
  -H "Content-Type: application/json" \
  -d '{"rigNumber":1,"driverName":"TestDriver","termsAccepted":true,"safetyAccepted":true}'
```

**Get Leaderboard**:
```bash
curl http://localhost:8080/api/leaderboard/daily
```

**Get Calendar**:
```bash
curl http://localhost:8080/api/calendar/current
```

## Troubleshooting

### Session Not Creating
- Check database file exists: `data/f1_telemetry.db`
- Verify calendar JSON files present
- Check Flask logs for errors

### Leaderboard Empty
- Ensure sessions have `Session_Status__c = 'Completed'`
- Check `Best_Lap_Time__c` is not NULL
- Verify date filters (daily/monthly)

### QR Codes Not Showing
- Check qrcodejs library loaded
- Verify network connectivity
- Check browser console for errors

### Session Not Ending
- Confirm F1 game sending SEND event
- Check receiver.py event handling
- Verify sessionId passed to /data endpoint

## Future Enhancements

- [ ] Lap-by-lap history storage (Lap_Record__c)
- [ ] Multi-session race weekends (Practice/Quali/Race)
- [ ] Driver profiles and statistics
- [ ] Achievements and badges
- [ ] Social sharing of best laps
- [ ] Live dual-rig comparison view
- [ ] Photo capture at race completion
- [ ] Email/SMS lap time notifications

## Support

For issues or questions:
- Check logs: Flask terminal output
- Database issues: `sqlite3 data/f1_telemetry.db`
- Review CLAUDE.md for system architecture
