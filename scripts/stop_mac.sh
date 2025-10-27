#!/bin/bash

# F1 Simulator System - Mac Stop Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping F1 Simulator System...${NC}"

# Kill processes by PID files if they exist
if [ -f /tmp/f1-flask.pid ]; then
    FLASK_PID=$(cat /tmp/f1-flask.pid)
    kill $FLASK_PID 2>/dev/null && echo -e "${GREEN}Stopped Flask Server (PID: $FLASK_PID)${NC}" || echo -e "${RED}Flask process not found${NC}"
    rm -f /tmp/f1-flask.pid
fi

if [ -f /tmp/f1-rig1.pid ]; then
    RIG1_PID=$(cat /tmp/f1-rig1.pid)
    kill $RIG1_PID 2>/dev/null && echo -e "${GREEN}Stopped Rig 1 Receiver (PID: $RIG1_PID)${NC}" || echo -e "${RED}Rig 1 process not found${NC}"
    rm -f /tmp/f1-rig1.pid
fi

if [ -f /tmp/f1-rig2.pid ]; then
    RIG2_PID=$(cat /tmp/f1-rig2.pid)
    kill $RIG2_PID 2>/dev/null && echo -e "${GREEN}Stopped Rig 2 Receiver (PID: $RIG2_PID)${NC}" || echo -e "${RED}Rig 2 process not found${NC}"
    rm -f /tmp/f1-rig2.pid
fi

# Force kill any remaining processes on these ports
echo -e "${YELLOW}Checking for stray processes...${NC}"
lsof -ti :8080 | xargs kill -9 2>/dev/null && echo -e "${GREEN}Killed process on port 8080${NC}" || true
lsof -ti :20777 | xargs kill -9 2>/dev/null && echo -e "${GREEN}Killed process on port 20777${NC}" || true
lsof -ti :20778 | xargs kill -9 2>/dev/null && echo -e "${GREEN}Killed process on port 20778${NC}" || true

echo -e "${GREEN}All services stopped${NC}"
