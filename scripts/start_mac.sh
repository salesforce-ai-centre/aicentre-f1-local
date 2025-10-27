#!/bin/bash

# F1 Simulator System - Mac Launcher
# Starts Flask server and both UDP receivers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}F1 Simulator System - Mac Setup${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r config/requirements.txt
else
    source venv/bin/activate
fi

# Check if database directory exists
if [ ! -d "data" ]; then
    echo -e "${YELLOW}Creating data directory...${NC}"
    mkdir -p data
fi

# Kill any existing processes on the ports
echo -e "${YELLOW}Checking for existing processes...${NC}"
lsof -ti :8080 | xargs kill -9 2>/dev/null || true
lsof -ti :20777 | xargs kill -9 2>/dev/null || true
lsof -ti :20778 | xargs kill -9 2>/dev/null || true

echo ""
echo -e "${GREEN}Starting F1 Simulator System...${NC}"
echo ""

# Start Flask server in background
echo -e "${YELLOW}[1/3] Starting Flask Web Server (port 8080)...${NC}"
python3 src/app.py > logs/flask.log 2>&1 &
FLASK_PID=$!
echo -e "${GREEN}       Flask PID: $FLASK_PID${NC}"

# Wait a moment for Flask to start
sleep 2

# Start Receiver for Rig 1
echo -e "${YELLOW}[2/3] Starting UDP Receiver - Rig 1 (port 20777)...${NC}"
python3 src/receiver.py --url http://localhost:8080/data --driver "Rig 1" --port 20777 --rig 1 > logs/receiver-rig1.log 2>&1 &
RIG1_PID=$!
echo -e "${GREEN}       Rig 1 Receiver PID: $RIG1_PID${NC}"

# Start Receiver for Rig 2
echo -e "${YELLOW}[3/3] Starting UDP Receiver - Rig 2 (port 20778)...${NC}"
python3 src/receiver.py --url http://localhost:8080/data --driver "Rig 2" --port 20778 --rig 2 > logs/receiver-rig2.log 2>&1 &
RIG2_PID=$!
echo -e "${GREEN}       Rig 2 Receiver PID: $RIG2_PID${NC}"

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}System Started Successfully!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "Process IDs:"
echo -e "  Flask Server:    ${GREEN}$FLASK_PID${NC}"
echo -e "  Rig 1 Receiver:  ${GREEN}$RIG1_PID${NC}"
echo -e "  Rig 2 Receiver:  ${GREEN}$RIG2_PID${NC}"
echo ""
echo -e "URLs:"
echo -e "  Welcome Page:    ${GREEN}http://localhost:8080/${NC}"
echo -e "  Sim 1 Attract:   ${GREEN}http://localhost:8080/attract?rig=1${NC}"
echo -e "  Sim 2 Attract:   ${GREEN}http://localhost:8080/attract?rig=2${NC}"
echo -e "  Dual Dashboard:  ${GREEN}http://localhost:8080/dual${NC}"
echo ""
echo -e "  ${YELLOW}On Network:${NC}"
echo -e "  Sim 1 Attract:   ${GREEN}http://172.18.159.209:8080/attract?rig=1${NC}"
echo -e "  Sim 2 Attract:   ${GREEN}http://172.18.159.209:8080/attract?rig=2${NC}"
echo ""
echo -e "Logs:"
echo -e "  Flask:           ${YELLOW}tail -f logs/flask.log${NC}"
echo -e "  Rig 1 Receiver:  ${YELLOW}tail -f logs/receiver-rig1.log${NC}"
echo -e "  Rig 2 Receiver:  ${YELLOW}tail -f logs/receiver-rig2.log${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Save PIDs to file for stop script
echo "$FLASK_PID" > /tmp/f1-flask.pid
echo "$RIG1_PID" > /tmp/f1-rig1.pid
echo "$RIG2_PID" > /tmp/f1-rig2.pid

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping all services...${NC}"
    kill $FLASK_PID 2>/dev/null || true
    kill $RIG1_PID 2>/dev/null || true
    kill $RIG2_PID 2>/dev/null || true
    rm -f /tmp/f1-*.pid
    echo -e "${GREEN}All services stopped${NC}"
    exit 0
}

# Trap Ctrl+C
trap cleanup INT TERM

# Wait for all background processes
wait
