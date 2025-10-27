#!/bin/bash

# Stream Deck START Button
# Switches both sims from attract screen to F1 game

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🏁 STARTING RACE${NC}"
echo ""

# Call API to trigger race start
curl -s -X POST http://localhost:8080/api/control/start-race

echo ""
echo -e "${GREEN}✓ Race started on both sims${NC}"
echo ""
echo "Sims should now switch to F1 game window"
