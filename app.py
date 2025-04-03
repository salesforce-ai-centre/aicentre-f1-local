import os
import json
import time
import queue
import threading
from flask import Flask, render_template, request, Response, jsonify, abort

app = Flask(__name__)

# Thread-safe queue to hold messages for SSE clients
# We store the *full* JSON payload string here
message_queue = queue.Queue()

# Store the latest full data payload (as dict) for new clients
latest_data = {}
data_lock = threading.Lock() # To protect access to latest_data

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
    app.logger.debug(f"Received data: {json.dumps(data)[:200]}...") # Log snippet

    # --- Data Enrichment & Event Detection (Server-Side) ---
    # You can add logic here to compare current data with latest_data
    # to generate specific event messages before broadcasting.

    global latest_data
    event_to_send = None # Specific event object to add to payload

    with data_lock:
        # Check for Lap Completion
        if data.get("lapCompleted") and not latest_data.get("lapCompleted", False):
             if data.get("lastLapTime") is not None and data.get("lapNumber", 0) > 1:
                 lap_num = data.get("lapNumber", 1) - 1 # Lap that was *just* completed
                 lap_time_str = format_time_ms(data.get("lastLapTime") * 1000) # Requires format_time_ms helper
                 event_to_send = {"message": f"Lap {lap_num} completed: {lap_time_str}", "type": "lap"}
                 app.logger.info(f"Event Detected: Lap {lap_num} completed")

        # TODO: Detect other events:
        # - Penalties (Requires Participant/Event packets data in payload)
        # - Flag changes (Requires CarStatus m_vehicleFiaFlags in payload)
        # - Major damage changes (Compare current damage to latest_data)
        # - Pit entry/exit (Requires LapData m_pitStatus in payload)

        # Update latest data *after* comparison
        latest_data = data.copy() # Store the received data

    # Add the detected event to the payload *if* one was generated
    if event_to_send:
        data["event"] = event_to_send

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
    """Server-Sent Events endpoint."""
    def event_stream():
        # Immediately send the latest known data to the new client
        with data_lock:
             current_state = latest_data.copy() # Get current state safely

        if current_state:
            try:
                yield f"data: {json.dumps(current_state)}\n\n"
            except TypeError as e:
                 app.logger.error(f"Error serializing initial state to JSON: {e}")

        # Then listen for new messages from the queue
        q = queue.Queue() # Create a local queue for this client
        # TODO: Need a way to register/deregister client queues globally
        # For simplicity now, we'll just read from the shared queue directly
        # This isn't scalable for many clients but works for a few.
        # A better approach involves listener management (Flask-SSE, etc.)

        while True:
            try:
                # Block waiting for a new message from the main queue
                data_json = message_queue.get(timeout=None) # Blocks indefinitely
                yield f"data: {data_json}\n\n"
                message_queue.task_done() # Mark task as complete
                app.logger.debug("Sent data via SSE")
            except queue.Empty:
                # This shouldn't happen with timeout=None, but handle defensively
                time.sleep(0.1)
                continue
            except Exception as e:
                # Log errors but try to keep the stream alive if possible
                 app.logger.error(f"Error in SSE stream loop: {e}", exc_info=True)
                 # Consider breaking the loop on certain errors
                 # yield f"event: error\ndata: {json.dumps({'message': 'Stream error occurred'})}\n\n"


    return Response(event_stream(), mimetype="text/event-stream")

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
    port = int(os.environ.get("PORT", 5000))
    # Run with gunicorn in production (Procfile), debug=False
    # For local development run: flask run --debug
    # Host '0.0.0.0' is important for Docker/Heroku environments
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True) # Use threaded for queue handling