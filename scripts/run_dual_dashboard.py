#!/usr/bin/env python3
"""
Launch dual-rig F1 telemetry dashboard with WebSocket support
"""

import sys
import os
import signal

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from app_dual_rig import start_server, gateway
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def signal_handler(sig, frame):
    """Handle shutdown gracefully"""
    logger.info("\n\nShutting down dual-rig dashboard...")
    gateway.stop()
    sys.exit(0)


if __name__ == '__main__':
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start the server
        start_server()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        gateway.stop()
        sys.exit(1)
