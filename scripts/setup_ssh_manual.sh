#!/bin/bash

# Manual SSH Key Setup
# Run each command one at a time

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Manual SSH Key Setup${NC}"
echo ""
echo -e "${YELLOW}Step 1: Copy key to Sim 1${NC}"
echo "Run this command and enter password 'Salesforce1' when prompted:"
echo ""
echo "  cat ~/.ssh/id_rsa.pub | ssh sim1admin@192.168.8.22 'mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys'"
echo ""
echo -e "${YELLOW}Step 2: Copy key to Sim 2${NC}"
echo "Run this command and enter password 'Salesforce1' when prompted:"
echo ""
echo "  cat ~/.ssh/id_rsa.pub | ssh sim2admin@192.168.8.21 'mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys'"
echo ""
echo -e "${YELLOW}Step 3: Test connection to Sim 1 (should not ask for password)${NC}"
echo "  ssh sim1admin@192.168.8.22 'echo Connection successful!'"
echo ""
echo -e "${YELLOW}Step 4: Test connection to Sim 2 (should not ask for password)${NC}"
echo "  ssh sim2admin@192.168.8.21 'echo Connection successful!'"
echo ""
