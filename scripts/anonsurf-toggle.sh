
---

### 2. Automation Script (`anonsurf-toggle.sh`)

This script is designed to be "production-ready." It includes input validation, colored output for readability, and the crucial automated DNS fix we discovered during troubleshooting.

Create a file named `scripts/anonsurf-toggle.sh` in your repo and paste the code below.

```bash
#!/bin/bash

# ==============================================================================
# Script: anonsurf-toggle.sh
# Description: Automates starting/stopping AnonSurf and fixes DNS symlink issues.
# ==============================================================================

# Define colors for terminal output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Ensure the script is run with sudo/root privileges
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[!] Error: Please run this script with sudo.${NC}"
  echo "Usage: sudo $0 [start|stop]"
  exit 1
fi

# Capture the first argument passed to the script
ACTION=$1

# ==========================================
# START LOGIC
# ==========================================
if [ "$ACTION" == "start" ]; then
    echo -e "${YELLOW}[*] Starting AnonSurf and routing traffic through Tor...${NC}"
    
    # Execute AnonSurf start command
    anonsurf start
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[+] AnonSurf started successfully.${NC}"
        echo -e "${YELLOW}[*] Please wait ~30 seconds for Tor to establish the circuit.${NC}"
        echo -e "${YELLOW}[*] Verify with: curl -s https://check.torproject.org/api/ip${NC}"
    else
        echo -e "${RED}[!] Failed to start AnonSurf.${NC}"
    fi

# ==========================================
# STOP LOGIC
# ==========================================
elif [ "$ACTION" == "stop" ]; then
    echo -e "${YELLOW}[*] Stopping AnonSurf...${NC}"
    
    # Execute AnonSurf stop command
    anonsurf stop
    
    echo -e "${YELLOW}[*] Restoring Ubuntu 24.04 systemd-resolved DNS symlink...${NC}"
    # Remove the broken static file created by AnonSurf
    rm -f /etc/resolv.conf
    # Recreate the correct symlink for systemd-resolved
    ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
    # Restart the DNS resolver service to apply changes
    systemctl restart systemd-resolved
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[+] DNS restored successfully.${NC}"
    else
        echo -e "${RED}[!] Failed to restart systemd-resolved.${NC}"
    fi
    
    echo -e "${YELLOW}[*] Testing internet connectivity...${NC}"
    # Send a quick ping to verify clearnet access is back
    if ping -c 2 google.com &> /dev/null; then
        echo -e "${GREEN}[+] Internet connection restored. You are back on Clearnet.${NC}"
    else
        echo -e "${RED}[!] Warning: Internet connectivity test failed. You may need to restart NetworkManager:${NC}"
        echo -e "${YELLOW}    sudo systemctl restart NetworkManager${NC}"
    fi

# ==========================================
# USAGE / HELP LOGIC
# ==========================================
else
    echo -e "${YELLOW}Usage: sudo $0 [start|stop]${NC}"
    echo "  start : Routes all traffic through Tor using AnonSurf."
    echo "  stop  : Stops AnonSurf and automatically fixes the DNS resolver."
    exit 1
fi
