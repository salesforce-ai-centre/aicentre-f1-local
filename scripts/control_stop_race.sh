#!/bin/bash

# Stream Deck STOP Button
# Ends race and shows results

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🏁 STOPPING RACE${NC}"
echo ""

# Call API to trigger race stop
curl -s -X POST http://localhost:8080/api/control/stop-race

echo ""
echo -e "${GREEN}✓ Race stopped - showing results${NC}"
