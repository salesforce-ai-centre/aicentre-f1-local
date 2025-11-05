"""
Dual-rig F1 telemetry dashboard with WebSocket support
"""

import os
import logging
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from dotenv import load_dotenv

from telemetry_gateway import TelemetryGateway, RigConfig
from websocket_publisher import WebSocketPublisher
from config import DEFAULT_SERVER_PORT, DEFAULT_SERVER_HOST

# Load environment variables
load_dotenv()

# Configure logging - write to both file and console
log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'telemetry.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w'),  # Write to file (overwrite on restart)
        logging.StreamHandler()  # Also write to console
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"📝 Logging to file: {log_file}")

# Get the parent directory of src/ which contains templates and static folders
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Initialize Flask app
app = Flask(__name__,
            template_folder=os.path.join(parent_dir, 'templates'),
            static_folder=os.path.join(parent_dir, 'static'))

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'f1-telemetry-secret-key')

# Initialize SocketIO with threading (more stable than eventlet)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    logger=False,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25
)

# Configure rigs
rigs = [
    RigConfig(
        rig_id="RIG_A",
        udp_port=20777,
        driver_name=os.environ.get("DRIVER_A_NAME", "Driver A"),
        device_id="SIM_A",
        individual_id=os.environ.get("DRIVER_A_INDIVIDUAL_ID")
    ),
    RigConfig(
        rig_id="RIG_B",
        udp_port=20778,
        driver_name=os.environ.get("DRIVER_B_NAME", "Driver B"),
        device_id="SIM_B",
        individual_id=os.environ.get("DRIVER_B_INDIVIDUAL_ID")
    )
]

# Initialize components
ws_publisher = WebSocketPublisher(socketio)

# Create gateway with WebSocket callback
gateway = TelemetryGateway(
    rigs=rigs,
    event_callback=ws_publisher.on_telemetry_packet
)


# --- Routes ---

@app.route('/')
def index():
    """Serve dual-rig dashboard"""
    return render_template('dual_rig_dashboard.html', rigs=rigs)


@app.route('/health')
def health():
    """Health check endpoint"""
    gateway_status = gateway.get_status()
    ws_stats = ws_publisher.get_stats()

    return jsonify({
        'status': 'healthy',
        'gateway': gateway_status,
        'websocket': ws_stats
    })


@app.route('/api/rigs')
def get_rigs():
    """Get rig configuration"""
    return jsonify({
        'rigs': [
            {
                'rig_id': rig.rig_id,
                'driver_name': rig.driver_name,
                'udp_port': rig.udp_port,
                'device_id': rig.device_id
            } for rig in rigs
        ]
    })


def start_server(host=DEFAULT_SERVER_HOST, port=None):
    """Start the dual-rig dashboard server"""
    if port is None:
        port = int(os.environ.get("PORT", DEFAULT_SERVER_PORT))

    # Start telemetry gateway
    logger.info("Starting telemetry gateway...")
    gateway.start()

    # Disable Flask's default logger for cleaner output
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.ERROR)

    logger.info("=" * 80)
    logger.info(f"🏎️  DUAL-RIG F1 TELEMETRY DASHBOARD")
    logger.info("=" * 80)
    logger.info(f"Dashboard: http://{host}:{port}")
    logger.info(f"Health Check: http://{host}:{port}/health")
    logger.info("")
    logger.info("Listening for telemetry from:")
    for rig in rigs:
        logger.info(f"  {'🔴' if rig.rig_id == 'RIG_A' else '🔵'} {rig.rig_id}: "
                   f"UDP port {rig.udp_port} ({rig.driver_name})")
    logger.info("")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 80)

    # Start Flask with SocketIO
    socketio.run(
        app,
        host=host,
        port=port,
        debug=False,
        use_reloader=False  # Important: prevents double-start
    )


if __name__ == '__main__':
    try:
        start_server()
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
        gateway.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        gateway.stop()
