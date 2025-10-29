import os
import json
import time
import queue
import threading
import random
import base64
import subprocess
import concurrent.futures
import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from flask import Flask, render_template, request, Response, jsonify, abort
from dotenv import load_dotenv

from config import (
    AI_ENABLED, MIN_AI_MESSAGE_INTERVAL_SECONDS, MAX_AI_MESSAGE_HISTORY,
    DAMAGE_THRESHOLD_PERCENT, TIRE_WEAR_CRITICAL_PERCENT, TIRE_WEAR_SEVERE_PERCENT,
    FUEL_LOW_LAPS_THRESHOLD, FUEL_STRATEGY_TRIGGER_CHANCE, TIRE_STRATEGY_TRIGGER_CHANCE,
    PERFORMANCE_COACHING_CHANCE, PERIODIC_STRATEGY_CHANCE, TIRE_WEAR_EVENT_CHANCE,
    PERIODIC_STRATEGY_MIN_INTERVAL, DEFAULT_SERVER_PORT, DEFAULT_SERVER_HOST
)
from datacloud_integration import create_datacloud_client

# Load environment variables from .env file if present
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the parent directory of src/ which contains templates and static folders
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__,
            template_folder=os.path.join(parent_dir, 'templates'),
            static_folder=os.path.join(parent_dir, 'static'))

# Data Cloud integration setup
datacloud_client = None
DATACLOUD_ENABLED = os.environ.get("DATACLOUD_ENABLED", "false").lower() == "true"

# Simulator SSH configuration (for window control)
SIM1_SSH_HOST = os.environ.get("SIM1_SSH_HOST", "sim1admin@192.168.8.22")
SIM2_SSH_HOST = os.environ.get("SIM2_SSH_HOST", "sim2admin@192.168.8.21")

if DATACLOUD_ENABLED:
    SALESFORCE_DOMAIN = os.environ.get("SALESFORCE_DOMAIN", "")
    SF_CLIENT_ID = os.environ.get("SF_CLIENT_ID", "")
    SF_PRIVATE_KEY_PATH = os.environ.get("SF_PRIVATE_KEY_PATH", "")
    SF_USERNAME = os.environ.get("SF_USERNAME", "")

    required_vars = {
        "SALESFORCE_DOMAIN": SALESFORCE_DOMAIN,
        "SF_CLIENT_ID": SF_CLIENT_ID,
        "SF_PRIVATE_KEY_PATH": SF_PRIVATE_KEY_PATH,
        "SF_USERNAME": SF_USERNAME
    }

    missing = [key for key, value in required_vars.items() if not value]

    if not missing:
        try:
            datacloud_client = create_datacloud_client(
                salesforce_domain=SALESFORCE_DOMAIN,
                client_id=SF_CLIENT_ID,
                private_key_path=SF_PRIVATE_KEY_PATH,
                username=SF_USERNAME,
                debug=True
            )
            logger.info(f"Data Cloud JWT integration enabled for domain: {SALESFORCE_DOMAIN}")
            logger.info(f"Authenticating as user: {SF_USERNAME}")
        except Exception as e:
            logger.error(f"Failed to initialize Data Cloud client: {e}")
            datacloud_client = None
    else:
        logger.warning(f"Data Cloud integration disabled. Missing: {', '.join(missing)}")
else:
    logger.info("Data Cloud integration disabled")

# AI Race Engineer configuration
SALESFORCE_CLIENT_SECRET = os.environ.get("SF_CLIENT_SECRET", "")
SALESFORCE_MODEL_VARIATIONS = [
    "sfdc_ai__DefaultGPT4Omni",
    "sfdc_ai__GPT4Omni",
    "gpt-4o",
    "sfdc_ai__DefaultAzureOpenAIGPT35Turbo",
    "sfdc_ai__AzureOpenAIGPT35Turbo"
]
SALESFORCE_MODEL_NAME = SALESFORCE_MODEL_VARIATIONS[0]
LAST_AI_MESSAGE_TIME = 0
LAST_AI_MESSAGE_TIME_LOCK = threading.Lock()  # Thread safety for AI message timing
AI_MESSAGE_HISTORY = []
AI_MESSAGE_HISTORY_LOCK = threading.Lock()  # Thread safety for message history

# Salesforce Models API validation
if AI_ENABLED:
    SF_CLIENT_ID = os.environ.get("SF_CLIENT_ID", "")
    SALESFORCE_DOMAIN = os.environ.get("SALESFORCE_DOMAIN", "")

    if not SF_CLIENT_ID or not SALESFORCE_CLIENT_SECRET:
        logger.warning("AI Race Engineer disabled: Missing SF_CLIENT_ID or SF_CLIENT_SECRET")
    else:
        logger.info(f"AI Race Engineer enabled with model: {SALESFORCE_MODEL_NAME}")
        logger.info(f"Salesforce domain: {SALESFORCE_DOMAIN}")
else:
    logger.info("AI Race Engineer disabled")

# Thread-safe queue to hold messages for SSE clients
# We store the *full* JSON payload string here
message_queue = queue.Queue()

# Store the latest full data payload (as dict) for new clients
latest_data = {}
data_lock = threading.Lock() # To protect access to latest_data

# AI processing thread pool for async operations
ai_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="AI-Worker")
pending_ai_tasks = {}  # Track pending AI tasks by type to avoid duplicates

# --- Event Detection Helper Functions ---

def _detect_lap_completion(data: Dict[str, Any], latest_data: Dict[str, Any], current_time: float) -> Optional[Dict[str, str]]:
    """
    Detect lap completion and generate event.

    Args:
        data: Current telemetry payload
        latest_data: Previous telemetry payload
        current_time: Current timestamp

    Returns:
        Event dictionary with message and type, or None if no lap completed
    """
    if data.get("lapCompleted") and not latest_data.get("lapCompleted", False):
        if data.get("lastLapTime") is not None and data.get("lapNumber", 0) > 1:
            lap_num = data.get("lapNumber", 1) - 1
            lap_time_str = format_time_ms(data.get("lastLapTime") * 1000)
            logger.info(f"Lap {lap_num} completed: {lap_time_str}")

            # Trigger AI feedback if enabled
            if AI_ENABLED and (current_time - LAST_AI_MESSAGE_TIME >= MIN_AI_MESSAGE_INTERVAL_SECONDS):
                lap_data = {
                    "lapTime": data.get("lastLapTime"),
                    "lapNumber": lap_num,
                    "previousLapTime": latest_data.get("lastLapTime")
                }
                generate_ai_coach_message_async("lap_completed", lap_data, data.get("sessionId"))

            return {"message": f"Lap {lap_num} completed: {lap_time_str}", "type": "lap"}
    return None


def _detect_ai_events(data: Dict[str, Any], latest_data: Dict[str, Any], current_time: float, last_ai_time: float) -> float:
    """
    Detect various racing events and trigger AI coaching.

    Args:
        data: Current telemetry payload
        latest_data: Previous telemetry payload
        current_time: Current timestamp
        last_ai_time: Timestamp of last AI message

    Returns:
        Updated last_ai_time if any event was triggered, otherwise returns input last_ai_time
    """
    session_id = data.get("sessionId")

    # Fuel strategy detection
    if _should_trigger_fuel_strategy(data, latest_data):
        current_fuel = data.get("fuelInTank", 0)
        lap_number = data.get("lapNumber", 0)
        fuel_used = latest_data.get("fuelInTank", 0) - current_fuel
        laps_remaining = current_fuel / fuel_used if fuel_used > 0 else 999

        strategy_data = {
            "fuelRemaining": current_fuel,
            "estimatedLapsLeft": laps_remaining,
            "lapNumber": lap_number,
            "fuelConsumption": fuel_used
        }
        generate_ai_coach_message_async("fuel_strategy", strategy_data, session_id)
        logger.info("Fuel strategy event triggered")
        return current_time

    # Tire strategy detection
    tire_strategy_result = _should_trigger_tire_strategy(data)
    if tire_strategy_result:
        max_wear, worn_tires = tire_strategy_result
        generate_ai_coach_message_async("tire_strategy", {
            "maxWear": max_wear,
            "wornTires": worn_tires,
            "lapNumber": data.get("lapNumber", 0)
        }, session_id)
        logger.info("Tire strategy event triggered")
        return current_time

    # Damage detection
    damage_data = _detect_significant_damage(data, latest_data)
    if damage_data:
        generate_ai_coach_message_async("damage_detected", damage_data, session_id)
        logger.info("Damage event triggered")
        return current_time

    # Tire wear warning
    wear_data = _detect_high_tire_wear(data)
    if wear_data:
        generate_ai_coach_message_async("tire_wear", wear_data, session_id)
        logger.info("Tire wear event triggered")
        return current_time

    # Performance coaching
    if _should_trigger_performance_coaching(data):
        sector = data.get("sector", 0)
        coaching_data = {
            "sector": sector + 1,
            "lapTime": data.get("lapTimeSoFar", 0),
            "speed": data.get("speed", {}).get("current", 0),
            "throttle": data.get("throttle", {}).get("current", 0),
            "brake": data.get("brake", {}).get("current", 0)
        }
        generate_ai_coach_message_async("performance_coaching", coaching_data, session_id)
        logger.info("Performance coaching event triggered")
        return current_time

    # Periodic strategic advice
    elapsed_time = current_time - last_ai_time
    if elapsed_time > PERIODIC_STRATEGY_MIN_INTERVAL and random.random() < PERIODIC_STRATEGY_CHANCE:
        generate_ai_coach_message_async("strategy", {
            "position": data.get("position", 0),
            "lapNumber": data.get("lapNumber", 0),
            "speed": data.get("speed", {}).get("current", 0),
            "trackName": data.get("track", "")
        }, session_id)
        logger.info("Periodic strategy event triggered")
        return current_time

    # DRS availability
    if data.get("drsAllowed") and not latest_data.get("drsAllowed"):
        generate_ai_coach_message_async("drs_available", {}, session_id)
        logger.info("DRS available event triggered")
        return current_time

    return last_ai_time


def _should_trigger_fuel_strategy(data, latest_data):
    """Check if fuel strategy alert should be triggered"""
    if not data.get("fuelInTank") or not data.get("lapNumber"):
        return False

    current_fuel = data.get("fuelInTank", 0)
    lap_number = data.get("lapNumber", 0)

    if not latest_data.get("fuelInTank") or lap_number <= latest_data.get("lapNumber", 0):
        return False

    fuel_used = latest_data.get("fuelInTank", 0) - current_fuel
    if fuel_used <= 0:
        return False

    laps_remaining = current_fuel / fuel_used
    return laps_remaining < FUEL_LOW_LAPS_THRESHOLD and random.random() < FUEL_STRATEGY_TRIGGER_CHANCE


def _should_trigger_tire_strategy(data):
    """Check if tire strategy alert should be triggered"""
    if not data.get("tyreWear") or not data.get("lapNumber"):
        return None

    max_wear = 0
    worn_tires = {}

    for tire in ["frontLeft", "frontRight", "rearLeft", "rearRight"]:
        wear = data.get("tyreWear", {}).get(tire, 0)
        if wear > max_wear:
            max_wear = wear
        if wear > TIRE_WEAR_CRITICAL_PERCENT / 100:
            worn_tires[tire] = wear

    if max_wear > TIRE_WEAR_SEVERE_PERCENT / 100 and random.random() < TIRE_STRATEGY_TRIGGER_CHANCE:
        return (max_wear, worn_tires)

    return None


def _detect_significant_damage(data, latest_data):
    """Detect significant damage increases"""
    if not data.get("damage") or not latest_data.get("damage"):
        return None

    damage_data = {}
    components = ["frontLeftWing", "frontRightWing", "rearWing", "floor", "gearBox", "engine"]

    for component in components:
        current = data.get("damage", {}).get(component, 0)
        previous = latest_data.get("damage", {}).get(component, 0)
        if current > previous + DAMAGE_THRESHOLD_PERCENT:
            damage_data[component] = current

    return damage_data if damage_data else None


def _detect_high_tire_wear(data):
    """Detect high tire wear"""
    if not data.get("tyreWear"):
        return None

    tire_wear = data.get("tyreWear", {})
    wear_data = {}

    for tire in ["frontLeft", "frontRight", "rearLeft", "rearRight"]:
        wear = tire_wear.get(tire, 0)
        if wear > TIRE_WEAR_CRITICAL_PERCENT / 100:
            wear_data[tire] = wear

    if wear_data and random.random() < TIRE_WEAR_EVENT_CHANCE:
        return wear_data

    return None


def _should_trigger_performance_coaching(data):
    """Check if performance coaching should be triggered"""
    if not data.get("sector") or not data.get("lapTimeSoFar"):
        return False

    sector = data.get("sector", 0)
    lap_time_so_far = data.get("lapTimeSoFar", 0)

    return sector >= 1 and lap_time_so_far > 0 and random.random() < PERFORMANCE_COACHING_CHANCE


# --- Routes ---

@app.route('/')
def index():
    """Serves the welcome/admin navigation page."""
    return render_template('welcome.html')

@app.route('/dashboard')
def dashboard():
    """Serves the single-rig dashboard (legacy route for debugging)."""
    return render_template('index.html')

@app.route('/thank-you')
def thank_you():
    """Serves the thank you/success page after form submission."""
    return render_template('thank_you.html')

@app.route('/dual')
def dual_dashboard():
    """Serves the dual-rig dashboard showing both simulators side-by-side."""
    # Get active sessions for both rigs
    from services.session_service import get_session_service

    session_service = get_session_service()
    rig1_session = session_service.get_active_session_for_rig(1)
    rig2_session = session_service.get_active_session_for_rig(2)

    rigs = [
        {
            'rig_number': 1,
            'driver_name': rig1_session.Driver_Name__c if rig1_session else 'Waiting...',
            'session_id': rig1_session.Id if rig1_session else None
        },
        {
            'rig_number': 2,
            'driver_name': rig2_session.Driver_Name__c if rig2_session else 'Waiting...',
            'session_id': rig2_session.Id if rig2_session else None
        }
    ]

    return render_template('dual_rig_dashboard.html', rigs=rigs)

@app.route('/attract')
def attract_screen():
    """Serves the attract/holding screen with QR code and leaderboards for a specific rig."""
    # Check if rig parameter is provided, otherwise show error
    rig = request.args.get('rig', type=int)
    if not rig or rig not in [1, 2]:
        return """
        <html>
        <body style="font-family: Arial; padding: 50px; text-align: center;">
            <h1>⚠️ Missing Rig Parameter</h1>
            <p>Please specify which simulator this is:</p>
            <p><a href="/attract?rig=1" style="display: inline-block; margin: 10px; padding: 20px 40px; background: #ff6b6b; color: white; text-decoration: none; border-radius: 10px; font-size: 20px;">Simulator 1 (Left)</a></p>
            <p><a href="/attract?rig=2" style="display: inline-block; margin: 10px; padding: 20px 40px; background: #4ecdc4; color: white; text-decoration: none; border-radius: 10px; font-size: 20px;">Simulator 2 (Right)</a></p>
        </body>
        </html>
        """, 400
    return render_template('attract_screen_single.html')

@app.route('/start')
def start_session_page():
    """Serves the session start page (QR code landing page)."""
    return render_template('start_session.html')

@app.route('/summary/<session_id>')
def session_summary(session_id):
    """Serves the session summary page."""
    return render_template('session_summary.html')

@app.route('/data', methods=['POST'])
def receive_data():
    """
    Endpoint to receive telemetry data from the local Python script.
    Puts the data into the queue for SSE broadcasting.
    """
    if not request.is_json:
        logger.warning("Received non-JSON request to /data")
        abort(400, description="Request must be JSON")

    data = request.get_json()
    # Disable logging for performance

    # --- Session Management Integration ---
    from services.session_service import get_session_service

    # Check for session-related events
    session_event_code = data.get('event', {}).get('eventCode') if isinstance(data.get('event'), dict) else None
    session_id = request.args.get('sessionId')  # Session ID passed from receiver

    if session_event_code == 'SEND':
        # Session ended - complete the session
        if session_id:
            try:
                session_service = get_session_service()
                session_service.complete_session(session_id)
                logger.info(f"Session {session_id} completed via SEND event")
                data['sessionCompleted'] = True
            except Exception as e:
                logger.error(f"Failed to complete session {session_id}: {e}")

    # Update session with telemetry if session ID provided
    if session_id and session_event_code != 'SEND':
        try:
            session_service = get_session_service()
            session_service.update_session_telemetry(session_id, data)
        except Exception as e:
            logger.debug(f"Session telemetry update failed: {e}")

    # --- Event Detection & AI Coaching ---
    global latest_data, LAST_AI_MESSAGE_TIME
    event_to_send = None
    current_time = time.time()

    with data_lock:
        # Check for lap completion
        event_to_send = _detect_lap_completion(data, latest_data, current_time)

        # AI-powered event detection (only if AI is enabled)
        # Check AI timing with thread-safe lock
        should_check_ai = False
        with LAST_AI_MESSAGE_TIME_LOCK:
            if AI_ENABLED and (current_time - LAST_AI_MESSAGE_TIME >= MIN_AI_MESSAGE_INTERVAL_SECONDS):
                should_check_ai = True

        if should_check_ai:
            new_last_time = _detect_ai_events(data, latest_data, current_time, LAST_AI_MESSAGE_TIME)
            with LAST_AI_MESSAGE_TIME_LOCK:
                LAST_AI_MESSAGE_TIME = new_last_time

        # Update latest data *after* comparisons
        latest_data = data.copy()

    # Add the detected event to the payload if one was generated
    if event_to_send:
        data["event"] = event_to_send
    
    # AI messages are now handled asynchronously and sent separately
    # This prevents blocking the main telemetry flow

    # Send to Data Cloud if enabled
    if datacloud_client:
        try:
            # Send telemetry record
            datacloud_client.send_telemetry_record(data)
            
            # Send race events if detected
            if event_to_send:
                event_to_send["sessionId"] = data.get("sessionId", "")
                event_to_send["driverName"] = data.get("driverName", "")
                event_to_send["lapNumber"] = data.get("lapNumber", 0)
                datacloud_client.send_race_event(event_to_send)
            
            # Send session info on first telemetry of session
            if data.get("lapNumber", 0) == 1 and data.get("sector", 0) == 0:
                datacloud_client.send_session_info(data)
                
        except Exception as e:
            logger.error(f"Failed to send data to Data Cloud: {e}")

    # Convert back to JSON string for the queue
    try:
        json_data = json.dumps(data)
        message_queue.put(json_data) # Put the full JSON string into the queue
    except TypeError as e:
        logger.error(f"Error serializing data to JSON: {e}. Data: {data}")
        return jsonify({"status": "error", "message": "Failed to serialize data"}), 500

    return jsonify({"status": "success", "message": "Data received"}), 200


@app.route('/stream')
def stream():
    """High-performance Server-Sent Events endpoint optimized for local operation."""
    def event_stream():
        # Set low-latency headers for SSE connection
        # Flask will add these to the response
        
        # Immediately send the latest known data to the new client
        with data_lock:
             current_state = latest_data.copy() # Get current state safely

        if current_state:
            try:
                yield f"data: {json.dumps(current_state)}\n\n"
            except TypeError as e:
                 logger.error(f"Error serializing initial state to JSON: {e}")

        # Maximum performance mode for local machine
        # Skip individual queue - direct access for local operation is fine
        # This wouldn't work with multiple clients but is optimal for local-only use

        while True:
            try:
                # Use an extremely short timeout for ultra-responsive local operation 
                try:
                    data_json = message_queue.get(timeout=0.001)
                    yield f"data: {data_json}\n\n"
                    message_queue.task_done()
                except queue.Empty:
                    # For local operation, yield an empty ping to keep connection alive
                    # and avoid browser connection timeout
                    yield ":\n\n"  # This is an SSE comment that browsers will ignore
                    continue
            except Exception as e:
                logger.error(f"Error in SSE stream: {e}", exc_info=True)
                yield f"event: error\ndata: {{\"error\": \"{str(e)}\"}}\n\n"
                # Keep the connection going

    # Set headers for optimal SSE performance
    response = Response(event_stream(), mimetype="text/event-stream")
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'  # Disable proxy buffering
    return response


# --- Session Management API Endpoints (Salesforce REST API pattern) ---

@app.route('/api/session', methods=['POST'])
def create_session():
    """
    Create a new session (Salesforce REST: POST /services/data/vXX.X/sobjects/Session__c)
    Request body: {rigNumber, driverName, termsAccepted, safetyAccepted}
    """
    from services.session_service import get_session_service

    if not request.is_json:
        return jsonify({"success": False, "error": "Request must be JSON"}), 400

    data = request.get_json()

    # Validate required fields
    required_fields = ['rigNumber', 'driverName', 'termsAccepted', 'safetyAccepted']
    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({
            "success": False,
            "error": f"Missing required fields: {', '.join(missing)}"
        }), 400

    try:
        session_service = get_session_service()
        session = session_service.create_waiting_session(
            rig_number=data['rigNumber'],
            driver_name=data['driverName'],
            terms_accepted=data['termsAccepted'],
            safety_accepted=data['safetyAccepted']
        )

        logger.info(f"Created session {session.Id} for {session.Driver_Name__c} on Rig {session.Rig_Number__c}")

        return jsonify({
            "success": True,
            "id": session.Id,
            "sessionName": session.Name,
            "rigNumber": session.Rig_Number__c,
            "trackName": session.Track_Name__c,
            "raceName": session.Race_Name__c
        }), 201

    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/session/<session_id>/start', methods=['POST'])
def start_session(session_id):
    """
    Start a session (Custom Apex REST endpoint pattern)
    Transitions session from Waiting to Active
    """
    from services.session_service import get_session_service

    try:
        session_service = get_session_service()
        session = session_service.start_session(session_id)

        logger.info(f"Started session {session.Id} for {session.Driver_Name__c}")

        return jsonify({
            "success": True,
            "id": session.Id,
            "status": session.Session_Status__c,
            "startTime": session.Session_Start_Time__c.isoformat() if session.Session_Start_Time__c else None
        }), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        logger.error(f"Failed to start session: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/session/<session_id>/complete', methods=['POST'])
def complete_session_endpoint(session_id):
    """
    Complete a session (Custom Apex REST endpoint pattern)
    Transitions session from Active to Completed
    """
    from services.session_service import get_session_service

    try:
        session_service = get_session_service()
        session = session_service.complete_session(session_id)

        logger.info(f"Completed session {session.Id} for {session.Driver_Name__c}")

        # Get session summary for response
        summary = session_service.get_session_summary(session_id)

        return jsonify({
            "success": True,
            "id": session.Id,
            "status": session.Session_Status__c,
            "summary": summary
        }), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        logger.error(f"Failed to complete session: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """
    Get session details (Salesforce REST: GET /services/data/vXX.X/sobjects/Session__c/:id)
    """
    from repositories.session_repository import SessionRepository

    try:
        session_repo = SessionRepository()
        session = session_repo.get_by_id(session_id)

        if not session:
            return jsonify({"success": False, "error": "Session not found"}), 404

        return jsonify({
            "success": True,
            "session": session.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Failed to get session: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/session/active/<int:rig_number>', methods=['GET'])
def get_active_session(rig_number):
    """
    Get active session for a rig (Custom query endpoint)
    """
    from services.session_service import get_session_service

    try:
        session_service = get_session_service()
        session = session_service.get_active_session_for_rig(rig_number)

        if not session:
            return jsonify({
                "success": True,
                "hasActiveSession": False,
                "session": None
            }), 200

        return jsonify({
            "success": True,
            "hasActiveSession": True,
            "session": session.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Failed to get active session: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/leaderboard/<period>', methods=['GET'])
def get_leaderboard(period):
    """
    Get leaderboard (SOQL query pattern)
    Periods: daily, monthly, track
    Query params: track (for track-specific leaderboards)
    """
    from repositories.session_repository import SessionRepository

    try:
        session_repo = SessionRepository()
        track_name = request.args.get('track')
        limit = int(request.args.get('limit', 10))

        if period == 'daily':
            leaderboard = session_repo.get_leaderboard_daily(track_name, limit)
        elif period == 'monthly':
            leaderboard = session_repo.get_leaderboard_monthly(track_name, limit)
        elif period == 'track':
            if not track_name:
                return jsonify({
                    "success": False,
                    "error": "track parameter required for track leaderboard"
                }), 400
            leaderboard = session_repo.get_leaderboard_track(track_name, limit)
        else:
            return jsonify({
                "success": False,
                "error": f"Invalid period: {period}. Use 'daily', 'monthly', or 'track'"
            }), 400

        return jsonify({
            "success": True,
            "period": period,
            "trackName": track_name,
            "records": leaderboard
        }), 200

    except Exception as e:
        logger.error(f"Failed to get leaderboard: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/calendar/current', methods=['GET'])
def get_current_race():
    """
    Get current F1 race from calendar
    """
    from services.calendar_service import get_calendar_service

    try:
        calendar_service = get_calendar_service()
        summary = calendar_service.get_calendar_summary()

        return jsonify({
            "success": True,
            "calendar": summary
        }), 200

    except Exception as e:
        logger.error(f"Failed to get calendar: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# --- Stream Deck Control Endpoints ---

@app.route('/api/control/start-race', methods=['POST'])
def control_start_race():
    """
    Stream Deck START button: Broadcast race start event to all browsers
    Chrome extension will handle window switching on sim PCs
    """
    try:
        logger.info("🏁 Stream Deck: Starting race - broadcasting to all browsers")

        # Broadcast race start event via SSE to all connected browsers
        event_data = {
            "event": "raceStarting",
            "rigs": [1, 2],
            "timestamp": datetime.now().isoformat()
        }

        # Add to message queue for SSE broadcasting
        message_queue.put(json.dumps(event_data))

        logger.info(f"Broadcasted race start event: {event_data}")

        return jsonify({
            "success": True,
            "message": "Race start signal sent - browsers will trigger window switch"
        }), 200

    except Exception as e:
        logger.error(f"Failed to start race: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/control/stop-race', methods=['POST'])
def control_stop_race():
    """
    Stream Deck STOP button: End race and show results
    """
    from services.session_service import get_session_service

    try:
        logger.info("🏁 Stream Deck: Stopping race - showing results")

        session_service = get_session_service()

        # Complete active sessions
        rig1_session = session_service.get_active_session_for_rig(1)
        rig2_session = session_service.get_active_session_for_rig(2)

        completed = []
        if rig1_session:
            session_service.complete_session(rig1_session.Id)
            completed.append(1)
        if rig2_session:
            session_service.complete_session(rig2_session.Id)
            completed.append(2)

        return jsonify({
            "success": True,
            "message": "Race stopped",
            "completedRigs": completed
        }), 200

    except Exception as e:
        logger.error(f"Failed to stop race: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/control/restart', methods=['POST'])
def control_restart():
    """
    Stream Deck RESTART button: Reset everything to attract screens
    """
    import subprocess
    from services.session_service import get_session_service

    try:
        logger.info("🔄 Stream Deck: Restarting - returning to attract screens")

        # Complete any active sessions first
        session_service = get_session_service()
        rig1_session = session_service.get_active_session_for_rig(1)
        rig2_session = session_service.get_active_session_for_rig(2)

        if rig1_session:
            session_service.complete_session(rig1_session.Id)
        if rig2_session:
            session_service.complete_session(rig2_session.Id)

        # Switch Sim 1 browser to attract screen
        try:
            subprocess.Popen([
                "ssh", SIM1_SSH_HOST,
                "DISPLAY=:0 wmctrl -a 'Chrome' && xdotool key F5"
            ], stderr=subprocess.DEVNULL)
        except Exception as e:
            logger.warning(f"Failed to refresh Sim 1 browser: {e}")

        # Switch Sim 2 browser to attract screen
        try:
            subprocess.Popen([
                "ssh", SIM2_SSH_HOST,
                "DISPLAY=:0 wmctrl -a 'Chrome' && xdotool key F5"
            ], stderr=subprocess.DEVNULL)
        except Exception as e:
            logger.warning(f"Failed to refresh Sim 2 browser: {e}")

        return jsonify({
            "success": True,
            "message": "System restarted - back to attract screens"
        }), 200

    except Exception as e:
        logger.error(f"Failed to restart: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# --- Helper Functions ---
def format_time_ms(time_in_ms):
    """Formats milliseconds into MM:SS.mmm"""
    if time_in_ms is None or time_in_ms <= 0:
        return "--:--.---"
    try:
        seconds_total = time_in_ms / 1000.0
        minutes = int(seconds_total // 60)
        seconds = int(seconds_total % 60)
        milliseconds = int((seconds_total * 1000) % 1000)
        return f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
    except Exception:
        return "--:--.---"

def generate_ai_coach_message_async(event_type, data, session_id=None):
    """
    Generate an AI coach message asynchronously using the Salesforce Models API.
    
    Args:
        event_type: Type of event (lap_completed, damage_detected, tire_wear, strategy, drs_available)
        data: Dictionary containing relevant data for the event
        session_id: Session identifier to track the request
    
    Returns:
        Future that resolves to Dictionary with messageType and messageText
    """
    def _generate_ai_message():
        try:
            # Check for recent similar messages to avoid repetition
            for recent_msg in AI_MESSAGE_HISTORY:
                if recent_msg.get("messageType") == event_type:
                    # If we've sent this type of message recently, reduce chance of sending again
                    if random.random() < 0.6:  # 60% chance to skip similar recent messages
                        logger.info(f"Skipping {event_type} message to avoid repetition")
                        return None
            
            # Create prompt based on event type
            prompt = create_prompt_for_event(event_type, data)
            
            # Call the Salesforce Models API
            message = call_models_api(prompt, data)
            logger.info(f"Successfully generated AI message for {event_type}")
            
            # Return the formatted message
            ai_message = {
                "messageType": get_message_type_label(event_type),
                "messageText": message
            }
            
            # Send the AI message to clients via a separate data push
            if session_id:
                ai_payload = {
                    "sessionId": session_id,
                    "aiCoach": ai_message,
                    "timestamp": time.time()
                }
                
                try:
                    json_data = json.dumps(ai_payload)
                    message_queue.put(json_data)
                    logger.info(f"AI message queued for session {session_id}")
                except Exception as e:
                    logger.error(f"Failed to queue AI message: {e}")
            
            return ai_message
            
        except Exception as e:
            logger.error(f"Error generating AI coach message: {e}", exc_info=True)
            return None
        finally:
            # Remove from pending tasks
            if event_type in pending_ai_tasks:
                del pending_ai_tasks[event_type]
    
    # Check if we already have a pending task for this event type
    if event_type in pending_ai_tasks and not pending_ai_tasks[event_type].done():
        logger.info(f"AI task for {event_type} already pending, skipping")
        return pending_ai_tasks[event_type]
    
    # Submit the task to the thread pool
    future = ai_executor.submit(_generate_ai_message)
    pending_ai_tasks[event_type] = future
    
    return future

def generate_ai_coach_message(event_type, data):
    """
    Legacy synchronous wrapper for backward compatibility.
    This should only be used for immediate responses where blocking is acceptable.
    """
    try:
        # Check for recent similar messages to avoid repetition
        for recent_msg in AI_MESSAGE_HISTORY:
            if recent_msg.get("messageType") == event_type:
                # If we've sent this type of message recently, reduce chance of sending again
                if random.random() < 0.6:  # 60% chance to skip similar recent messages
                    logger.info(f"Skipping {event_type} message to avoid repetition")
                    return None
        
        # Create prompt based on event type
        prompt = create_prompt_for_event(event_type, data)
        
        # Call the Salesforce Models API
        try:
            message = call_models_api(prompt, data)
            logger.info(f"Successfully generated AI message for {event_type}")
            
            # Return the formatted message
            return {
                "messageType": get_message_type_label(event_type),
                "messageText": message
            }
        except Exception as api_error:
            logger.error(f"API call error for {event_type}: {api_error}")
            # Instead of falling back, we'll propagate the error
            raise
    except Exception as e:
        logger.error(f"Error generating AI coach message: {e}", exc_info=True)
        raise Exception(f"Failed to generate coach message: {e}")

def get_message_type_label(event_type):
    """Convert event type to user-friendly label"""
    labels = {
        "lap_completed": "Lap Time",
        "damage_detected": "Damage",
        "tire_wear": "Tires",
        "tire_strategy": "Tire Strategy",
        "fuel_strategy": "Fuel Strategy", 
        "performance_coaching": "Coaching",
        "strategy": "Strategy",
        "drs_available": "DRS",
        "default": "Race Engineer"
    }
    return labels.get(event_type, labels["default"])

def create_prompt_for_event(event_type, data):
    """Create appropriate prompt for the Models API based on event type and data"""
    
    base_prompt = """You are an F1 race engineer providing coaching advice over team radio to a driver.
    
    COMMUNICATION STYLE:
    - Keep your message brief and conversational (30-60 words)
    - Use realistic F1 team radio language with appropriate terminology
    - Sound like a professional race engineer (knowledgeable but focused)
    - Use some radio-style phrases like "Copy that", "Box this lap", "Push now", etc.
    - Occasionally address the driver in a personal way with encouragement
    - Sound slightly urgent and focused like real team radio
    
    CONTENT REQUIREMENTS:
    - Focus on practical advice the driver can use immediately
    - Be specific rather than general when possible
    - Base recommendations on the telemetry data provided
    - Include numerical values when relevant (braking points, throttle percentages, etc.)
    - Balance technical information with actionable instructions
    """
    
    if event_type == "lap_completed":
        lap_time = data.get("lapTime", 0)
        previous_time = data.get("previousLapTime", 0)
        lap_number = data.get("lapNumber", 1)
        
        # Calculate improvement/deterioration
        improvement = ""
        if previous_time and lap_time:
            diff = previous_time - lap_time
            if diff > 0:
                improvement = f"You've improved by {abs(diff):.2f} seconds compared to your previous lap."
            else:
                improvement = f"You're {abs(diff):.2f} seconds slower than your previous lap."
        
        prompt = f"""{base_prompt}
        CONTEXT:
        The driver just completed lap {lap_number} with a time of {lap_time:.2f} seconds.
        {improvement}
        
        TASK:
        Give specific feedback on their lap time and one clear, actionable suggestion to improve for the next lap.
        Mention a specific corner or section if possible. Use proper F1 team radio style communication.
        """
    
    elif event_type == "damage_detected":
        damaged_parts = []
        for part, value in data.items():
            if value > 50:
                severity = "severe"
            elif value > 30:
                severity = "moderate"
            else:
                severity = "minor"
            damaged_parts.append(f"{part} with {severity} damage ({value}%)")
        
        damaged_parts_text = ", ".join(damaged_parts)
        prompt = f"""{base_prompt}
        CONTEXT:
        The car has just sustained damage to: {damaged_parts_text}.
        
        TASK:
        Provide specific advice on how the driver should adjust their driving style to compensate for this damage.
        Include how this will affect car handling, and give specific corner approach modifications.
        Use urgent but calm team radio tone typical for damage situations.
        """
    
    elif event_type == "tire_wear":
        worn_tires = []
        for tire, wear in data.items():
            worn_tires.append(f"{tire}: {wear*100:.1f}% worn")
        
        worn_tires_text = ", ".join(worn_tires)
        prompt = f"""{base_prompt}
        CONTEXT:
        The driver's tires are showing significant wear: {worn_tires_text}.
        
        TASK:
        Provide specific tire management advice including:
        - How to adjust driving style (braking points, acceleration, etc.)
        - Whether they should consider pitting soon
        - Which corners to be especially careful with
        - How to maximize the remaining tire life
        Use authentic F1 team radio style for tire management communication.
        """
    
    elif event_type == "strategy":
        position = data.get("position", 0)
        lap_number = data.get("lapNumber", 0)
        track = data.get("trackName", "the track")
        
        prompt = f"""{base_prompt}
        CONTEXT:
        The driver is currently in position {position} on lap {lap_number} at {track}.
        
        TASK:
        Provide strategic race advice that incorporates:
        - Race position strategy (defense, attack, maintain gap)
        - Pace management recommendations
        - Information about competitors if relevant
        - Motivational element to keep the driver focused
        Use authentic race engineer strategic communication style.
        """
    
    elif event_type == "drs_available":
        prompt = f"""{base_prompt}
        CONTEXT:
        DRS has just been enabled and is now available when within 1 second of the car ahead in the DRS zones.
        
        TASK:
        Give the driver a quick reminder about:
        - How to use DRS effectively for overtaking
        - Where the DRS zones and detection points are on this track
        - Any specific strategy for getting within DRS range
        Use authentic F1 race engineer style for DRS communication.
        """
    
    elif event_type == "fuel_strategy":
        fuel_remaining = data.get("fuelRemaining", 0)
        laps_left = data.get("estimatedLapsLeft", 0)
        lap_number = data.get("lapNumber", 0)
        consumption = data.get("fuelConsumption", 0)
        
        prompt = f"""{base_prompt}
        CONTEXT:
        Current fuel situation: {fuel_remaining:.1f}kg remaining, estimated {laps_left:.1f} laps of fuel left.
        Current lap: {lap_number}, last lap consumption: {consumption:.2f}kg.
        
        TASK:
        Provide strategic fuel management advice including:
        - Recommended pit window timing
        - Fuel saving techniques if needed
        - Risk assessment of current fuel strategy
        - Specific driving style adjustments to optimize consumption
        Use authentic F1 team radio style for fuel strategy communication.
        """
    
    elif event_type == "tire_strategy":
        max_wear = data.get("maxWear", 0)
        worn_tires = data.get("wornTires", {})
        lap_number = data.get("lapNumber", 0)
        
        worn_tire_info = ", ".join([f"{tire}: {wear*100:.0f}%" for tire, wear in worn_tires.items()])
        
        prompt = f"""{base_prompt}
        CONTEXT:
        Tire degradation alert: Maximum wear at {max_wear*100:.0f}% on lap {lap_number}.
        Critical wear locations: {worn_tire_info}.
        
        TASK:
        Provide urgent tire strategy advice including:
        - Immediate pit stop recommendation or tire management strategy
        - Specific driving adjustments for tire preservation
        - Risk assessment of continuing on current tires
        - Optimal pit window timing
        Use urgent but professional F1 team radio style for critical tire situations.
        """
    
    elif event_type == "performance_coaching":
        sector = data.get("sector", 1)
        lap_time = data.get("lapTime", 0)
        speed = data.get("speed", 0)
        throttle = data.get("throttle", 0)
        brake = data.get("brake", 0)
        
        prompt = f"""{base_prompt}
        CONTEXT:
        Performance coaching for Sector {sector}. Current lap time: {lap_time:.2f}s.
        Current telemetry: Speed {speed}km/h, Throttle {throttle*100:.0f}%, Brake {brake*100:.0f}%.
        
        TASK:
        Provide specific driving technique coaching including:
        - Sector-specific improvement suggestions
        - Braking point and throttle application advice
        - Racing line optimization for this sector
        - Specific corner technique recommendations
        Use encouraging but technical F1 coaching style.
        """
    
    return prompt

def call_models_api(prompt, data):
    """
    Call the Salesforce Models API to generate a coaching message using the provided prompt
    """
    try:
        logger.info("Calling Salesforce Models API")
        
        # Standard Models API endpoint for GPT-4o
        url = f"https://api.salesforce.com/einstein/platform/v1/models/{SALESFORCE_MODEL_NAME}/generations"
        
        # Set up request headers with authentication
        headers = {
            "Content-Type": "application/json;charset=utf-8",
            "x-sfdc-app-context": "EinsteinGPT",
            "x-client-feature-id": "ai-platform-models-connected-app"
        }
        
        # Add authentication using basic auth with client ID and secret
        auth_str = f"{SALESFORCE_CLIENT_ID}:{SALESFORCE_CLIENT_SECRET}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        headers["Authorization"] = f"Basic {encoded_auth}"
        
        # Standard payload for text generation
        payload = {
            "prompt": prompt,
            "localization": {
                "defaultLocale": "en_US"
            }
        }
        
        # Log the complete prompt for debugging
        logger.info(f"PROMPT TO AI: {prompt}")
        print(f"\n--- AI REQUEST PROMPT ---\n{prompt}\n------------------------\n")
        
        # Make the API request
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            # If we get an error, try several authentication variations
            if response.status_code in [400, 401, 404]:
                logger.warning(f"Primary endpoint failed with status {response.status_code}. Trying authentication variations.")
                
                # The URL is correct, but we'll try different auth approaches
                alt_url = f"https://api.salesforce.com/einstein/platform/v1/models/{SALESFORCE_MODEL_NAME}/generations"
                
                # Different auth variations to try
                auth_variations = [
                    # Try 1: Auth header without "Basic" prefix
                    {
                        "description": "Direct token auth",
                        "headers": {
                            **headers,
                            "Authorization": headers["Authorization"].split()[1] if "Authorization" in headers and " " in headers["Authorization"] else headers.get("Authorization", "")
                        }
                    },
                    # Try 2: Using client ID and secret as separate parameters
                    {
                        "description": "Separate client credentials",
                        "headers": {
                            **{k: v for k, v in headers.items() if k != "Authorization"},
                            "x-client-id": SALESFORCE_CLIENT_ID,
                            "x-client-secret": SALESFORCE_CLIENT_SECRET
                        }
                    },
                    # Try 3: Using OAuth Bearer
                    {
                        "description": "OAuth bearer format",
                        "headers": {
                            **headers,
                            "Authorization": f"Bearer {SALESFORCE_CLIENT_SECRET}"
                        }
                    }
                ]
                
                # Try each auth variation
                for variation in auth_variations:
                    try:
                        print(f"\n--- TRYING AUTH VARIATION: {variation['description']} ---\n")
                        alt_response = requests.post(alt_url, headers=variation['headers'], json=payload, timeout=10)
                        
                        if alt_response.status_code == 200 or alt_response.status_code == 201:
                            logger.info(f"Auth variation '{variation['description']}' succeeded!")
                            response = alt_response
                            break
                        else:
                            logger.warning(f"Auth variation '{variation['description']}' failed with status {alt_response.status_code}")
                    except Exception as var_error:
                        logger.error(f"Error with auth variation '{variation['description']}': {var_error}")
                        continue
                
                # If all auth variations failed, try different model names
                if response.status_code not in [200, 201]:
                    logger.warning("All auth variations failed. Trying different model names.")
                    
                    # Try all model variations after the first one (which we already tried)
                    for model_name in SALESFORCE_MODEL_VARIATIONS[1:]:
                        try:
                            model_url = f"https://api.salesforce.com/einstein/platform/v1/models/{model_name}/generations"
                            print(f"\n--- TRYING ALTERNATIVE MODEL: {model_name} ---\n")
                            
                            # Try with the original headers first
                            model_response = requests.post(model_url, headers=headers, json=payload, timeout=10)
                            
                            if model_response.status_code == 200 or model_response.status_code == 201:
                                logger.info(f"Model '{model_name}' succeeded!")
                                response = model_response
                                break
                            else:
                                logger.warning(f"Model '{model_name}' failed with status {model_response.status_code}")
                        except Exception as model_error:
                            logger.error(f"Error with model '{model_name}': {model_error}")
                            continue
        except Exception as req_error:
            logger.error(f"API request failed: {req_error}")
            raise Exception(f"Failed to connect to Salesforce Models API: {req_error}")
        
        # Handle API response
        if response.status_code == 200 or response.status_code == 201:
            # Print the raw response for debugging
            print(f"\n--- RAW API RESPONSE ---\n{response.text[:500]}\n------------------------\n")
            
            result = response.json()
            generated_text = ""
            
            # Parse response based on the endpoint format
            if "generation" in result:
                # Standard Models API format
                generated_text = result.get("generation", {}).get("generatedText", "")
            elif "predictions" in result:
                # Alternative endpoint format
                generated_text = result.get("predictions", [{}])[0].get("text", "")
            elif "result" in result and "completions" in result.get("result", {}):
                # LLM completions format
                generated_text = result.get("result", {}).get("completions", [{}])[0].get("text", "")
            
            if generated_text:
                logger.info("Successfully received AI generated response")
                print(f"\n--- AI RESPONSE ---\n{generated_text}\n------------------------\n")
                return generated_text
            else:
                error_msg = "API returned empty response"
                logger.error(error_msg)
                raise Exception(error_msg)
        else:
            error_message = f"API returned status code {response.status_code}: {response.text}"
            logger.error(error_message)
            print(f"\n--- API ERROR ---\n{error_message}\n------------------------\n")
            raise Exception(f"Salesforce API error: {response.status_code}")
        
    except requests.exceptions.Timeout:
        error_msg = "API request timed out"
        logger.error(error_msg)
        raise Exception(error_msg)
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise Exception(f"API request failed: {e}")
    except Exception as e:
        logger.error(f"Models API call failed: {e}", exc_info=True)
        raise Exception(f"Models API call failed: {e}")

# --- Payload Requirements ---
# The telemetry payload from receiver.py must include:
# - position, drsAllowed, ersStoreEnergy
# - damage fields (frontLeftWing, frontRightWing, etc.)
# - tyre data (temperatures, wear, pressures)
# See receiver.py _prepare_payload() for complete field list
#   Map these from `CarDamageData` in your `_prepare_payload` function.
# - Consider adding `m_vehicleFiaFlags` from CarStatusData for flag events.
# - Consider adding `m_pitStatus` from LapData for pit events.

# Example of adding damage to _prepare_payload in your *original* script:
"""
def _prepare_payload(self) -> Optional[Dict[str, Any]]:
    # ... (existing checks and data prep) ...
    if not self.latest_car_damage: return None # Add this check

    # ... (existing payload construction) ...

    payload["position"] = current_lap.m_carPosition + 1 # Often 0-based index
    payload["drsAllowed"] = current_status.m_drsAllowed
    payload["ersStoreEnergy"] = current_status.m_ersStoreEnergy
    # Add more from CarStatus as needed (FIA flags, fuel etc)

    # Add Damage Data
    current_damage = self.latest_car_damage
    payload["damage"] = {
        "frontLeftWing": current_damage.m_frontLeftWingDamage,
        "frontRightWing": current_damage.m_frontRightWingDamage,
        "rearWing": current_damage.m_rearWingDamage,
        "floor": current_damage.m_floorDamage,
        "diffuser": current_damage.m_diffuserDamage, # Add if needed
        "sidepod": current_damage.m_sidepodDamage,   # Add if needed
        "gearBox": current_damage.m_gearBoxDamage,
        "engine": current_damage.m_engineDamage,
        # Add tyre damage, DRS/ERS faults if needed
    }

    return payload
"""


if __name__ == '__main__':
    # Get port from environment variable (for cloud deployments like Heroku)
    port = int(os.environ.get("PORT", DEFAULT_SERVER_PORT))

    # Disable Flask's console logging for cleaner output
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.ERROR)

    logger.info(f"Starting F1 Telemetry Dashboard on {DEFAULT_SERVER_HOST}:{port}")
    app.run(host=DEFAULT_SERVER_HOST, port=port, debug=False, threaded=True)