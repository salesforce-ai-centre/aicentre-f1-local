import os
import json
import time
import queue
import threading
import requests
import random
import jwt
import base64
import concurrent.futures
from datetime import datetime, timedelta
from flask import Flask, render_template, request, Response, jsonify, abort
from dotenv import load_dotenv
from datacloud_integration import create_datacloud_client

# Load environment variables from .env file if present
load_dotenv()

app = Flask(__name__)

# Data Cloud integration
DATACLOUD_ENABLED = os.environ.get("DATACLOUD_ENABLED", "false").lower() == "true"
SALESFORCE_DOMAIN = os.environ.get("SALESFORCE_DOMAIN", "")
SF_CLIENT_ID = os.environ.get("SF_CLIENT_ID", "")
SF_PRIVATE_KEY_PATH = os.environ.get("SF_PRIVATE_KEY_PATH", "")
SF_USERNAME = os.environ.get("SF_USERNAME", "")
datacloud_client = None

if DATACLOUD_ENABLED and SALESFORCE_DOMAIN and SF_CLIENT_ID and SF_PRIVATE_KEY_PATH and SF_USERNAME:
    try:
        datacloud_client = create_datacloud_client(
            salesforce_domain=SALESFORCE_DOMAIN,
            client_id=SF_CLIENT_ID,
            private_key_path=SF_PRIVATE_KEY_PATH,
            username=SF_USERNAME,
            debug=True
        )
        print(f"Data Cloud JWT integration enabled for domain: {SALESFORCE_DOMAIN}")
        print(f"Authenticating as user: {SF_USERNAME}")
    except Exception as e:
        print(f"Failed to initialize Data Cloud client: {e}")
        datacloud_client = None
else:
    missing = []
    if not DATACLOUD_ENABLED:
        missing.append("DATACLOUD_ENABLED=true")
    if not SALESFORCE_DOMAIN:
        missing.append("SALESFORCE_DOMAIN")
    if not SF_CLIENT_ID:
        missing.append("SF_CLIENT_ID")
    if not SF_PRIVATE_KEY_PATH:
        missing.append("SF_PRIVATE_KEY_PATH")
    if not SF_USERNAME:
        missing.append("SF_USERNAME")
    
    if missing:
        print(f"Data Cloud integration disabled. Missing configuration: {', '.join(missing)}")
    else:
        print("Data Cloud integration disabled")

# Salesforce API configuration
SALESFORCE_DOMAIN = "ai-centre-uk.my.salesforce.com"
SALESFORCE_CLIENT_ID = os.environ.get("SF_CLIENT_ID", "")  # Set in environment or .env file
SALESFORCE_CLIENT_SECRET = os.environ.get("SF_CLIENT_SECRET", "")  # Set in environment or .env file

# Available model variations to try in order of preference
SALESFORCE_MODEL_VARIATIONS = [
    "sfdc_ai__DefaultGPT4Omni",        # Default naming convention
    "sfdc_ai__GPT4Omni",               # Alternative without "Default" prefix
    "gpt-4o",                          # Direct model name
    "sfdc_ai__DefaultAzureOpenAIGPT35Turbo",  # Fallback to GPT-3.5 if GPT-4o not available
    "sfdc_ai__AzureOpenAIGPT35Turbo"   # Alternative GPT-3.5
]

# Primary model to use
SALESFORCE_MODEL_NAME = SALESFORCE_MODEL_VARIATIONS[0]

# AI Race Engineer configuration
AI_ENABLED = False
MIN_AI_MESSAGE_INTERVAL = 15  # Minimum seconds between AI messages
LAST_AI_MESSAGE_TIME = 0
AI_MESSAGE_HISTORY = []  # Keep track of recent messages to avoid repetition
MAX_HISTORY_ITEMS = 5

# Salesforce Models API is disabled
if AI_ENABLED:
    if not SALESFORCE_CLIENT_ID or not SALESFORCE_CLIENT_SECRET:
        print("WARNING: Salesforce API credentials not found or incomplete.")
        print("Please set SF_CLIENT_ID and SF_CLIENT_SECRET in .env file")
        AI_ENABLED = False
    else:
        print(f"Using Salesforce Models API with model: {SALESFORCE_MODEL_NAME}")
        print(f"Salesforce domain: {SALESFORCE_DOMAIN}")
else:
    print("AI Race Engineer disabled")

# Thread-safe queue to hold messages for SSE clients
# We store the *full* JSON payload string here
message_queue = queue.Queue()

# Store the latest full data payload (as dict) for new clients
latest_data = {}
data_lock = threading.Lock() # To protect access to latest_data

# AI processing thread pool for async operations
ai_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="AI-Worker")
pending_ai_tasks = {}  # Track pending AI tasks by type to avoid duplicates

# --- Routes ---

@app.route('/')
def index():
    """Serves the main dashboard HTML page."""
    return render_template('index.html')

@app.route('/data', methods=['POST'])
def receive_data():
    """
    Endpoint to receive telemetry data from the local Python script.
    Puts the data into the queue for SSE broadcasting.
    """
    if not request.is_json:
        app.logger.warning("Received non-JSON request to /data")
        abort(400, description="Request must be JSON")

    data = request.get_json()
    # Disable logging for performance

    # --- Data Enrichment & Event Detection (Server-Side) ---
    # Event detection and AI coaching integration

    global latest_data, LAST_AI_MESSAGE_TIME, AI_MESSAGE_HISTORY
    event_to_send = None  # Event object to add to payload
    current_time = time.time()

    with data_lock:
        # Check for Lap Completion
        if data.get("lapCompleted") and not latest_data.get("lapCompleted", False):
             if data.get("lastLapTime") is not None and data.get("lapNumber", 0) > 1:
                 lap_num = data.get("lapNumber", 1) - 1  # Lap that was *just* completed
                 lap_time_str = format_time_ms(data.get("lastLapTime") * 1000)
                 event_to_send = {"message": f"Lap {lap_num} completed: {lap_time_str}", "type": "lap"}
                 app.logger.info(f"Event Detected: Lap {lap_num} completed")
                 
                 # Get AI feedback for completed lap (async)
                 if AI_ENABLED and (current_time - LAST_AI_MESSAGE_TIME >= MIN_AI_MESSAGE_INTERVAL):
                     lap_data = {
                         "lapTime": data.get("lastLapTime"),
                         "lapNumber": lap_num,
                         "previousLapTime": latest_data.get("lastLapTime")
                     }
                     # Start async AI generation - no blocking
                     generate_ai_coach_message_async("lap_completed", lap_data, data.get("sessionId"))
                     LAST_AI_MESSAGE_TIME = current_time  # Update timestamp to prevent duplicates

        # Enhanced proactive strategy detection
        
        # Fuel strategy alerts
        if AI_ENABLED and data.get("fuelInTank") and data.get("lapNumber") and (current_time - LAST_AI_MESSAGE_TIME >= MIN_AI_MESSAGE_INTERVAL):
            current_fuel = data.get("fuelInTank", 0)
            lap_number = data.get("lapNumber", 0)
            
            # Estimate fuel consumption if we have previous data
            if latest_data.get("fuelInTank") and lap_number > latest_data.get("lapNumber", 0):
                fuel_used = latest_data.get("fuelInTank", 0) - current_fuel
                if fuel_used > 0:
                    laps_remaining_with_fuel = current_fuel / fuel_used if fuel_used > 0 else 999
                    
                    # Pit stop strategy alert (async)
                    if laps_remaining_with_fuel < 8 and random.random() < 0.3:  # 30% chance when low fuel
                        strategy_data = {
                            "fuelRemaining": current_fuel,
                            "estimatedLapsLeft": laps_remaining_with_fuel,
                            "lapNumber": lap_number,
                            "fuelConsumption": fuel_used
                        }
                        generate_ai_coach_message_async("fuel_strategy", strategy_data, data.get("sessionId"))
                        LAST_AI_MESSAGE_TIME = current_time
                        app.logger.info(f"Event Detected: Fuel strategy recommendation (async)")

        # Tire performance degradation
        if AI_ENABLED and data.get("tyreWear") and data.get("lapNumber") and (current_time - LAST_AI_MESSAGE_TIME >= MIN_AI_MESSAGE_INTERVAL):
            max_wear = 0
            worn_tires = {}
            
            for tire in ["frontLeft", "frontRight", "rearLeft", "rearRight"]:
                wear = data.get("tyreWear", {}).get(tire, 0)
                if wear > max_wear:
                    max_wear = wear
                if wear > 0.7:  # 70% wear threshold
                    worn_tires[tire] = wear
            
            # Proactive tire strategy (async)
            if max_wear > 0.85 and random.random() < 0.4:  # 40% chance when tires very worn
                generate_ai_coach_message_async("tire_strategy", {
                    "maxWear": max_wear,
                    "wornTires": worn_tires,
                    "lapNumber": data.get("lapNumber", 0)
                }, data.get("sessionId"))
                LAST_AI_MESSAGE_TIME = current_time
                app.logger.info(f"Event Detected: Tire strategy recommendation (async)")

        # Performance coaching based on sector times
        if AI_ENABLED and data.get("sector") and data.get("lapTimeSoFar") and (current_time - LAST_AI_MESSAGE_TIME >= MIN_AI_MESSAGE_INTERVAL):
            # Coaching for slow sectors (simplified)
            sector = data.get("sector", 0)
            lap_time_so_far = data.get("lapTimeSoFar", 0)
            
            # If we're in sector 2 or 3 and going slower than expected (async)
            if sector >= 1 and lap_time_so_far > 0 and random.random() < 0.1:  # 10% chance for coaching
                coaching_data = {
                    "sector": sector + 1,  # Human-readable sector
                    "lapTime": lap_time_so_far,
                    "speed": data.get("speed", {}).get("current", 0),
                    "throttle": data.get("throttle", {}).get("current", 0),
                    "brake": data.get("brake", {}).get("current", 0)
                }
                generate_ai_coach_message_async("performance_coaching", coaching_data, data.get("sessionId"))
                LAST_AI_MESSAGE_TIME = current_time
                app.logger.info(f"Event Detected: Performance coaching (async)")

        # Detect significant damage changes and get AI feedback
        if AI_ENABLED and data.get("damage") and latest_data.get("damage") and (current_time - LAST_AI_MESSAGE_TIME >= MIN_AI_MESSAGE_INTERVAL):
            damage_increase = False
            damage_data = {}
            
            # Check if any damage component increased significantly
            for component in ["frontLeftWing", "frontRightWing", "rearWing", "floor", "gearBox", "engine"]:
                current = data.get("damage", {}).get(component, 0)
                previous = latest_data.get("damage", {}).get(component, 0)
                if current > previous + 15:  # 15% damage threshold
                    damage_increase = True
                    damage_data[component] = current
            
            if damage_increase:
                generate_ai_coach_message_async("damage_detected", damage_data, data.get("sessionId"))
                LAST_AI_MESSAGE_TIME = current_time
                app.logger.info(f"Event Detected: Significant damage increase (async)")
        
        # Detect tire wear issues
        if AI_ENABLED and data.get("tyreWear") and (current_time - LAST_AI_MESSAGE_TIME >= MIN_AI_MESSAGE_INTERVAL):
            tire_wear = data.get("tyreWear", {})
            high_wear = False
            wear_data = {}
            
            for tire in ["frontLeft", "frontRight", "rearLeft", "rearRight"]:
                wear = tire_wear.get(tire, 0)
                if wear > 0.7:  # 70% wear threshold
                    high_wear = True
                    wear_data[tire] = wear
            
            if high_wear and random.random() < 0.3:  # Only trigger occasionally for tire wear
                generate_ai_coach_message_async("tire_wear", wear_data, data.get("sessionId"))
                LAST_AI_MESSAGE_TIME = current_time
                app.logger.info(f"Event Detected: High tire wear (async)")
        
        # Periodic strategic advice (every 30-60 seconds)
        elapsed_time = current_time - LAST_AI_MESSAGE_TIME
        if AI_ENABLED and elapsed_time > 45 and random.random() < 0.2:  # 20% chance after 45 seconds
            generate_ai_coach_message_async("strategy", {
                "position": data.get("position", 0),
                "lapNumber": data.get("lapNumber", 0),
                "speed": data.get("speed", {}).get("current", 0),
                "trackName": data.get("track", "")
            }, data.get("sessionId"))
            LAST_AI_MESSAGE_TIME = current_time
            app.logger.info(f"Event: Providing periodic strategic advice (async)")

        # Handle DRS availability (async)
        if AI_ENABLED and data.get("drsAllowed") and not latest_data.get("drsAllowed") and (current_time - LAST_AI_MESSAGE_TIME >= MIN_AI_MESSAGE_INTERVAL):
            generate_ai_coach_message_async("drs_available", {}, data.get("sessionId"))
            LAST_AI_MESSAGE_TIME = current_time
            app.logger.info(f"Event Detected: DRS now available (async)")

        # Update latest data *after* comparison
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
            app.logger.error(f"Failed to send data to Data Cloud: {e}")

    # Convert back to JSON string for the queue
    try:
        json_data = json.dumps(data)
        message_queue.put(json_data) # Put the full JSON string into the queue
    except TypeError as e:
        app.logger.error(f"Error serializing data to JSON: {e}. Data: {data}")
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
                 app.logger.error(f"Error serializing initial state to JSON: {e}")

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
                app.logger.error(f"Error in SSE stream: {e}", exc_info=True)
                yield f"event: error\ndata: {{\"error\": \"{str(e)}\"}}\n\n"
                # Keep the connection going

    # Set headers for optimal SSE performance
    response = Response(event_stream(), mimetype="text/event-stream")
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'  # Disable proxy buffering
    return response

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

def get_auth_token():
    """
    Get an access token for Salesforce API.
    Tries multiple authentication methods:
    1. OAuth2 client credentials if we have a client ID and secret
    2. JWT token if that fails
    3. Direct consumer key and secret as a fallback
    
    Returns:
        String: Access token for API authorization
    """
    global ACCESS_TOKEN, TOKEN_EXPIRES_AT
    
    try:
        # Check if we have a valid cached token
        current_time = time.time()
        if ACCESS_TOKEN and current_time < TOKEN_EXPIRES_AT - 60:  # 1 minute buffer
            app.logger.info("Using cached access token")
            return ACCESS_TOKEN
        
        # Try OAuth2 client credentials flow first
        auth_url = "https://login.salesforce.com/services/oauth2/token"
        
        # Prepare the request body
        auth_data = {
            "grant_type": "client_credentials",
            "client_id": SALESFORCE_CLIENT_ID,
            "client_secret": SALESFORCE_CLIENT_SECRET
        }
        
        # Make the token request
        response = requests.post(auth_url, data=auth_data)
        
        # Check if we got a valid response
        if response.status_code == 200:
            result = response.json()
            ACCESS_TOKEN = result.get("access_token")
            expires_in = result.get("expires_in", 3600)  # Default to 1 hour
            TOKEN_EXPIRES_AT = current_time + expires_in
            
            app.logger.info(f"Successfully obtained OAuth token, expires in {expires_in} seconds")
            return ACCESS_TOKEN
            
        # If OAuth2 fails, try JWT token approach
        app.logger.warning(f"OAuth2 token request failed: {response.status_code} {response.text}")
        app.logger.info("Falling back to JWT token approach")
        
        # Create JWT payload according to Salesforce JWT requirements
        now = datetime.utcnow()
        exp_time = now + timedelta(minutes=5)  # Token expires in 5 minutes
        
        payload = {
            'iss': SALESFORCE_CLIENT_ID,        # Client ID from connected app
            'sub': SALESFORCE_DOMAIN,           # Your Salesforce domain
            'aud': 'https://login.salesforce.com',  # This is the auth endpoint
            'exp': int(exp_time.timestamp()),   # Expiration time in seconds
            'iat': int(now.timestamp()),        # Issued at time in seconds
        }
        
        # Print the payload for debugging
        print(f"\n--- JWT PAYLOAD ---\n{json.dumps(payload, indent=2)}\n------------------\n")
        
        # Encode the JWT
        token = jwt.encode(
            payload,
            SALESFORCE_CLIENT_SECRET,  # Client secret from connected app
            algorithm='HS256'
        )
        
        # Use the JWT token to request an access token
        jwt_auth_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": token
        }
        
        jwt_response = requests.post(auth_url, data=jwt_auth_data)
        
        if jwt_response.status_code == 200:
            jwt_result = jwt_response.json()
            ACCESS_TOKEN = jwt_result.get("access_token")
            jwt_expires_in = jwt_result.get("expires_in", 3600)
            TOKEN_EXPIRES_AT = current_time + jwt_expires_in
            
            app.logger.info(f"Successfully obtained JWT-based token, expires in {jwt_expires_in} seconds")
            return ACCESS_TOKEN
        
        # If all else fails, return the client ID itself as a last resort fallback
        app.logger.warning(f"JWT token request failed: {jwt_response.status_code} {jwt_response.text}")
        app.logger.info("Using client secret as direct token (last resort)")
        return SALESFORCE_CLIENT_SECRET
        
    except Exception as e:
        app.logger.error(f"Error getting authorization token: {e}", exc_info=True)
        return None

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
                        app.logger.info(f"Skipping {event_type} message to avoid repetition")
                        return None
            
            # Create prompt based on event type
            prompt = create_prompt_for_event(event_type, data)
            
            # Call the Salesforce Models API
            message = call_models_api(prompt, data)
            app.logger.info(f"Successfully generated AI message for {event_type}")
            
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
                    app.logger.info(f"AI message queued for session {session_id}")
                except Exception as e:
                    app.logger.error(f"Failed to queue AI message: {e}")
            
            return ai_message
            
        except Exception as e:
            app.logger.error(f"Error generating AI coach message: {e}", exc_info=True)
            return None
        finally:
            # Remove from pending tasks
            if event_type in pending_ai_tasks:
                del pending_ai_tasks[event_type]
    
    # Check if we already have a pending task for this event type
    if event_type in pending_ai_tasks and not pending_ai_tasks[event_type].done():
        app.logger.info(f"AI task for {event_type} already pending, skipping")
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
                    app.logger.info(f"Skipping {event_type} message to avoid repetition")
                    return None
        
        # Create prompt based on event type
        prompt = create_prompt_for_event(event_type, data)
        
        # Call the Salesforce Models API
        try:
            message = call_models_api(prompt, data)
            app.logger.info(f"Successfully generated AI message for {event_type}")
            
            # Return the formatted message
            return {
                "messageType": get_message_type_label(event_type),
                "messageText": message
            }
        except Exception as api_error:
            app.logger.error(f"API call error for {event_type}: {api_error}")
            # Instead of falling back, we'll propagate the error
            raise
    except Exception as e:
        app.logger.error(f"Error generating AI coach message: {e}", exc_info=True)
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
        app.logger.info("Calling Salesforce Models API")
        
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
        app.logger.info(f"PROMPT TO AI: {prompt}")
        print(f"\n--- AI REQUEST PROMPT ---\n{prompt}\n------------------------\n")
        
        # Make the API request
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            # If we get an error, try several authentication variations
            if response.status_code in [400, 401, 404]:
                app.logger.warning(f"Primary endpoint failed with status {response.status_code}. Trying authentication variations.")
                
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
                            app.logger.info(f"Auth variation '{variation['description']}' succeeded!")
                            response = alt_response
                            break
                        else:
                            app.logger.warning(f"Auth variation '{variation['description']}' failed with status {alt_response.status_code}")
                    except Exception as var_error:
                        app.logger.error(f"Error with auth variation '{variation['description']}': {var_error}")
                        continue
                
                # If all auth variations failed, try different model names
                if response.status_code not in [200, 201]:
                    app.logger.warning("All auth variations failed. Trying different model names.")
                    
                    # Try all model variations after the first one (which we already tried)
                    for model_name in SALESFORCE_MODEL_VARIATIONS[1:]:
                        try:
                            model_url = f"https://api.salesforce.com/einstein/platform/v1/models/{model_name}/generations"
                            print(f"\n--- TRYING ALTERNATIVE MODEL: {model_name} ---\n")
                            
                            # Try with the original headers first
                            model_response = requests.post(model_url, headers=headers, json=payload, timeout=10)
                            
                            if model_response.status_code == 200 or model_response.status_code == 201:
                                app.logger.info(f"Model '{model_name}' succeeded!")
                                response = model_response
                                break
                            else:
                                app.logger.warning(f"Model '{model_name}' failed with status {model_response.status_code}")
                        except Exception as model_error:
                            app.logger.error(f"Error with model '{model_name}': {model_error}")
                            continue
        except Exception as req_error:
            app.logger.error(f"API request failed: {req_error}")
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
                app.logger.info("Successfully received AI generated response")
                print(f"\n--- AI RESPONSE ---\n{generated_text}\n------------------------\n")
                return generated_text
            else:
                error_msg = "API returned empty response"
                app.logger.error(error_msg)
                raise Exception(error_msg)
        else:
            error_message = f"API returned status code {response.status_code}: {response.text}"
            app.logger.error(error_message)
            print(f"\n--- API ERROR ---\n{error_message}\n------------------------\n")
            raise Exception(f"Salesforce API error: {response.status_code}")
        
    except requests.exceptions.Timeout:
        error_msg = "API request timed out"
        app.logger.error(error_msg)
        raise Exception(error_msg)
    except requests.exceptions.RequestException as e:
        app.logger.error(f"API request failed: {e}")
        raise Exception(f"API request failed: {e}")
    except Exception as e:
        app.logger.error(f"Models API call failed: {e}", exc_info=True)
        raise Exception(f"Models API call failed: {e}")

# This section has been intentionally removed as we're only using the Salesforce Models API

# --- Payload Enrichment ---
# The payload from your original script needs to include fields used by the dashboard:
# - Ensure `position` (from LapData.m_carPosition) is included.
# - Ensure `drsAllowed` (from CarStatusData.m_drsAllowed) is included.
# - Ensure `ersStoreEnergy` (from CarStatusData.m_ersStoreEnergy) is included.
# - Include damage fields: `damage.frontLeftWing`, `damage.frontRightWing`, etc.
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
    # Get port from environment variable for Heroku
    port = int(os.environ.get("PORT", 8080))
    # Run with gunicorn in production (Procfile), debug=False
    # For local development run: flask run --debug
    # Host '0.0.0.0' is important for Docker/Heroku environments
    # Disable Flask console logging for production dashboard
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)