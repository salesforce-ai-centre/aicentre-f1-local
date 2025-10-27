#!/bin/bash

# Deploy configuration to Sim PCs
# Usage: ./scripts/deploy_to_sim.sh [1|2]

set -e

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 [1|2]"
    echo "  1 = Deploy to Sim 1 (192.168.8.22)"
    echo "  2 = Deploy to Sim 2 (192.168.8.21)"
    exit 1
fi

RIG=$1
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ "$RIG" = "1" ]; then
    SIM_IP="192.168.8.22"
    SIM_USER="sim1admin"
    UDP_PORT="20777"
    ATTRACT_URL="http://172.18.159.209:8080/attract?rig=1"
elif [ "$RIG" = "2" ]; then
    SIM_IP="192.168.8.21"
    SIM_USER="sim2admin"
    UDP_PORT="20778"
    ATTRACT_URL="http://172.18.159.209:8080/attract?rig=2"
else
    echo "Error: Rig must be 1 or 2"
    exit 1
fi

echo -e "${GREEN}Deploying to Sim $RIG ($SIM_IP)${NC}"
echo ""

# Test SSH connection
echo -e "${YELLOW}Testing SSH connection...${NC}"
if ssh -o ConnectTimeout=5 $SIM_USER@$SIM_IP "echo 'Connected'" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ SSH connection successful${NC}"
else
    echo -e "${YELLOW}⚠ SSH requires password or connection failed${NC}"
    echo "You may need to enter password: Salesforce1"
fi

echo ""
echo -e "${YELLOW}Installing required software...${NC}"
ssh $SIM_USER@$SIM_IP << 'EOF'
sudo apt update
sudo apt install -y wmctrl xdotool unclutter
EOF

echo ""
echo -e "${YELLOW}Creating Chrome autostart file...${NC}"
ssh $SIM_USER@$SIM_IP "mkdir -p ~/.config/autostart"

# Create the .desktop file
ssh $SIM_USER@$SIM_IP "cat > ~/.config/autostart/f1-attract.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=F1 Attract Screen - Rig $RIG
Exec=google-chrome --kiosk --incognito --disable-infobars --noerrdialogs --disable-session-crashed-bubble $ATTRACT_URL
Terminal=false
EOF

echo ""
echo -e "${YELLOW}Creating hide cursor autostart file...${NC}"
ssh $SIM_USER@$SIM_IP "cat > ~/.config/autostart/hide-cursor.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Hide Mouse Cursor
Exec=/usr/bin/unclutter -idle 0.1
Terminal=false
EOF

echo ""
echo -e "${GREEN}✓ Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "1. On Sim $RIG, configure F1 game:"
echo "   Settings → Telemetry → UDP IP: 172.18.159.209, Port: $UDP_PORT"
echo "2. Reboot Sim $RIG to test autostart"
echo "3. Verify attract screen appears: $ATTRACT_URL"
echo ""
