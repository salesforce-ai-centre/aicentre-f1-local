#!/bin/bash

# Stream Deck RESTART Button
# Returns everything to attract screens

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🔄 RESTARTING SYSTEM${NC}"
echo ""

# Call API to trigger restart
curl -s -X POST http://localhost:8080/api/control/restart

echo ""
echo -e "${GREEN}✓ System reset to attract screens${NC}"
