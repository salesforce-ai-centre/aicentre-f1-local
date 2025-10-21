"""
Configuration constants for F1 Telemetry Dashboard
Centralizes all magic numbers and configuration values
"""

# Flask Server Configuration
DEFAULT_SERVER_PORT = 8080
DEFAULT_SERVER_HOST = "0.0.0.0"

# AI Race Engineer Configuration
AI_ENABLED = False  # Toggle AI race engineer feature
MIN_AI_MESSAGE_INTERVAL_SECONDS = 15  # Minimum time between AI messages
MAX_AI_MESSAGE_HISTORY = 5  # Number of recent messages to track

# Event Detection Thresholds
DAMAGE_THRESHOLD_PERCENT = 15  # Significant damage increase threshold
TIRE_WEAR_CRITICAL_PERCENT = 70  # Tire wear warning threshold
TIRE_WEAR_SEVERE_PERCENT = 85  # Tire wear critical threshold
FUEL_LOW_LAPS_THRESHOLD = 8  # Trigger fuel strategy below this many laps

# Event Detection Probabilities (for non-critical events)
FUEL_STRATEGY_TRIGGER_CHANCE = 0.3  # 30% chance when fuel is low
TIRE_STRATEGY_TRIGGER_CHANCE = 0.4  # 40% chance when tires very worn
PERFORMANCE_COACHING_CHANCE = 0.1  # 10% chance for coaching
PERIODIC_STRATEGY_CHANCE = 0.2  # 20% chance for periodic advice
TIRE_WEAR_EVENT_CHANCE = 0.3  # 30% chance for tire wear events

# Timing Configuration
PERIODIC_STRATEGY_MIN_INTERVAL = 45  # Seconds before periodic strategy advice

# Data Cloud Configuration
DATACLOUD_BATCH_SIZE = 10  # Records per batch
DATACLOUD_BATCH_TIMEOUT_SECONDS = 2.0  # Max time before flushing batch

# UDP Receiver Configuration
DEFAULT_UDP_IP = "0.0.0.0"
DEFAULT_UDP_PORT = 20777
DEFAULT_SEND_INTERVAL_SECONDS = 0.01  # 10ms updates for local operation
SOCKET_TIMEOUT_SECONDS = 1.0

# Performance Monitoring
STATUS_LOG_INTERVAL_SECONDS = 30.0  # Log performance stats interval
LOG_THROTTLE_INTERVAL_SECONDS = 10.0  # Throttle debug log messages

# Dashboard Configuration
MAX_EVENT_LOG_ENTRIES = 20  # Maximum events to show in UI
MAX_AI_MESSAGES_DISPLAYED = 10  # Maximum AI messages to show
MAX_LAP_CHART_HISTORY = 20  # Laps to display in chart

# Gauge Configuration
SPEED_GAUGE_MAX_KMH = 350
SPEED_GAUGE_ANIMATION_SPEED = 32
RPM_GAUGE_MAX = 15000
RPM_GAUGE_ANIMATION_SPEED = 32

# G-Force Limits
MAX_G_FORCE = 2.0  # Clamp g-force display to ±2g

# Temperature Thresholds (Celsius)
TIRE_TEMP_OPTIMAL_MIN = 80
TIRE_TEMP_OPTIMAL_MAX = 105

# ERS Configuration
ERS_MAX_ENERGY_JOULES = 4000000  # 4MJ maximum

# SSE Configuration
SSE_QUEUE_TIMEOUT_SECONDS = 0.001  # Ultra-low latency for local operation
SSE_RECONNECT_BASE_DELAY_MS = 1000  # Base delay for exponential backoff
SSE_MAX_RECONNECT_DELAY_MS = 30000  # Maximum reconnection delay

# JWT Authentication
JWT_EXPIRY_SECONDS = 300  # 5 minutes
JWT_TOKEN_BUFFER_SECONDS = 60  # Re-authenticate 1 minute before expiry

# F1 Game Constants
NUM_CARS = 22  # Number of cars in F1 game
F1_25_PACKET_FORMAT = 2025
F1_24_PACKET_FORMAT = 2024

# Tire Array Index Mapping (F1 game uses: RL, RR, FL, FR)
TIRE_INDEX_REAR_LEFT = 0
TIRE_INDEX_REAR_RIGHT = 1
TIRE_INDEX_FRONT_LEFT = 2
TIRE_INDEX_FRONT_RIGHT = 3

# Fuel Mix Types
FUEL_MIX_LEAN = 0
FUEL_MIX_STANDARD = 1
FUEL_MIX_RICH = 2
FUEL_MIX_MAX = 3

# DRS States
DRS_INACTIVE = 0
DRS_ACTIVE = 1

# Pit Status
PIT_STATUS_NONE = 0
PIT_STATUS_PITTING = 1
PIT_STATUS_IN_PIT_AREA = 2
