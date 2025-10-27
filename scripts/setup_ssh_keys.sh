#!/bin/bash

# Setup SSH Keys for Passwordless Access to Sim PCs
# Password: Salesforce1

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Setting up SSH keys for sim PCs...${NC}"
echo ""

# Check if SSH key exists
if [ ! -f ~/.ssh/id_rsa ]; then
    echo -e "${YELLOW}Generating SSH key...${NC}"
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
else
    echo -e "${GREEN}SSH key already exists${NC}"
fi

echo ""
echo -e "${YELLOW}Copying SSH key to Sim 1 (192.168.8.22)...${NC}"
echo "Password: Salesforce1"
ssh-copy-id -i ~/.ssh/id_rsa.pub sim1admin@192.168.8.22

echo ""
echo -e "${YELLOW}Copying SSH key to Sim 2 (192.168.8.21)...${NC}"
echo "Password: Salesforce1"
ssh-copy-id -i ~/.ssh/id_rsa.pub sim2admin@192.168.8.21

echo ""
echo -e "${GREEN}Testing connections...${NC}"
echo ""

echo -e "${YELLOW}Testing Sim 1:${NC}"
ssh sim1admin@192.168.8.22 "echo '  ✓ Connection successful!' && hostname"

echo ""
echo -e "${YELLOW}Testing Sim 2:${NC}"
ssh sim2admin@192.168.8.21 "echo '  ✓ Connection successful!' && hostname"

echo ""
echo -e "${GREEN}SSH keys setup complete! You can now SSH without passwords.${NC}"
