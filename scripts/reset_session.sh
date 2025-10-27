#!/bin/bash

# Reset Session Script
# Completes active sessions and returns to attract screen

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

BASE_URL="${1:-http://localhost:8080}"

echo -e "${YELLOW}Resetting F1 Simulator Sessions...${NC}"
echo ""

# Check for active session on Rig 1
echo -e "${YELLOW}Checking Rig 1...${NC}"
RIG1_RESPONSE=$(curl -s "${BASE_URL}/api/session/active/1")
RIG1_HAS_SESSION=$(echo $RIG1_RESPONSE | grep -o '"hasActiveSession":true' || echo "")

if [ ! -z "$RIG1_HAS_SESSION" ]; then
    RIG1_SESSION_ID=$(echo $RIG1_RESPONSE | grep -o '"Id":"[^"]*"' | head -1 | cut -d'"' -f4)
    echo -e "  Found active session: ${GREEN}$RIG1_SESSION_ID${NC}"
    echo -e "  Completing session..."
    curl -s -X POST "${BASE_URL}/api/session/${RIG1_SESSION_ID}/complete" > /dev/null
    echo -e "  ${GREEN}✓ Session completed${NC}"
else
    echo -e "  ${YELLOW}No active session${NC}"
fi

echo ""

# Check for active session on Rig 2
echo -e "${YELLOW}Checking Rig 2...${NC}"
RIG2_RESPONSE=$(curl -s "${BASE_URL}/api/session/active/2")
RIG2_HAS_SESSION=$(echo $RIG2_RESPONSE | grep -o '"hasActiveSession":true' || echo "")

if [ ! -z "$RIG2_HAS_SESSION" ]; then
    RIG2_SESSION_ID=$(echo $RIG2_RESPONSE | grep -o '"Id":"[^"]*"' | head -1 | cut -d'"' -f4)
    echo -e "  Found active session: ${GREEN}$RIG2_SESSION_ID${NC}"
    echo -e "  Completing session..."
    curl -s -X POST "${BASE_URL}/api/session/${RIG2_SESSION_ID}/complete" > /dev/null
    echo -e "  ${GREEN}✓ Session completed${NC}"
else
    echo -e "  ${YELLOW}No active session${NC}"
fi

echo ""
echo -e "${GREEN}✓ Reset complete!${NC}"
echo ""
echo -e "Next steps:"
echo -e "  1. Browsers should automatically return to attract screen after 10 seconds"
echo -e "  2. Or manually navigate to:"
echo -e "     Rig 1: ${GREEN}${BASE_URL}/attract?rig=1${NC}"
echo -e "     Rig 2: ${GREEN}${BASE_URL}/attract?rig=2${NC}"
echo ""
