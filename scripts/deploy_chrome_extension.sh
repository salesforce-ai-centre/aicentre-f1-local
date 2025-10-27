#!/bin/bash

# Deploy Chrome Extension to Sim PCs
# Usage: ./scripts/deploy_chrome_extension.sh [1|2]

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
BLUE='\033[0;34m'
NC='\033[0m'

if [ "$RIG" = "1" ]; then
    SIM_IP="192.168.8.22"
    SIM_USER="sim1admin"
elif [ "$RIG" = "2" ]; then
    SIM_IP="192.168.8.21"
    SIM_USER="sim2admin"
else
    echo "Error: Rig must be 1 or 2"
    exit 1
fi

echo -e "${GREEN}Deploying Chrome Extension to Sim $RIG ($SIM_IP)${NC}"
echo ""

# Test SSH connection
echo -e "${YELLOW}Testing SSH connection...${NC}"
if ssh -o ConnectTimeout=5 $SIM_USER@$SIM_IP "echo 'Connected'" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ SSH connection successful${NC}"
else
    echo -e "${YELLOW}⚠ SSH requires password or connection failed${NC}"
    echo "Password: Salesforce1"
fi

echo ""
echo -e "${YELLOW}Step 1: Installing dependencies on Sim $RIG${NC}"
ssh $SIM_USER@$SIM_IP << 'EOF'
sudo apt update
sudo apt install -y wmctrl xdotool python3
which wmctrl && echo "✓ wmctrl installed"
which xdotool && echo "✓ xdotool installed"
which python3 && echo "✓ python3 installed"
EOF

echo ""
echo -e "${YELLOW}Step 2: Copying native host to Sim $RIG${NC}"
ssh $SIM_USER@$SIM_IP "sudo mkdir -p /usr/local/bin"
scp chrome-extension/native-host.py $SIM_USER@$SIM_IP:/tmp/f1-window-switcher
ssh $SIM_USER@$SIM_IP "sudo mv /tmp/f1-window-switcher /usr/local/bin/f1-window-switcher && sudo chmod +x /usr/local/bin/f1-window-switcher"
echo -e "${GREEN}✓ Native host installed${NC}"

echo ""
echo -e "${YELLOW}Step 3: Creating native messaging manifest${NC}"
ssh $SIM_USER@$SIM_IP << 'EOF'
mkdir -p ~/.config/google-chrome/NativeMessagingHosts/
cat > ~/.config/google-chrome/NativeMessagingHosts/com.f1.windowswitcher.json << 'MANIFEST'
{
  "name": "com.f1.windowswitcher",
  "description": "F1 Window Switcher for Simulators",
  "path": "/usr/local/bin/f1-window-switcher",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://EXTENSION_ID_WILL_BE_FILLED/"
  ]
}
MANIFEST
EOF
echo -e "${GREEN}✓ Native messaging manifest created${NC}"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Chrome Extension deployment complete for Sim $RIG!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Next steps (manual on Sim $RIG):${NC}"
echo ""
echo "1. Copy the chrome-extension folder to Sim $RIG:"
echo "   scp -r chrome-extension $SIM_USER@$SIM_IP:~/chrome-extension"
echo ""
echo "2. On Sim $RIG, open Chrome and go to: chrome://extensions/"
echo ""
echo "3. Enable 'Developer mode' (toggle in top-right)"
echo ""
echo "4. Click 'Load unpacked' and select: ~/chrome-extension"
echo ""
echo "5. Copy the Extension ID (looks like: abcdefghijklmnopqrstuvwxyz)"
echo ""
echo "6. Update the native messaging manifest with the Extension ID:"
echo "   nano ~/.config/google-chrome/NativeMessagingHosts/com.f1.windowswitcher.json"
echo "   Replace EXTENSION_ID_WILL_BE_FILLED with your actual ID"
echo ""
echo "7. Test in Chrome console (F12):"
echo "   F1Controller.test()"
echo "   F1Controller.switchToGame()"
echo ""
echo -e "${GREEN}If window switches to F1 game, installation is successful!${NC}"
echo ""
