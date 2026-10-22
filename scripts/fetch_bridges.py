#!/usr/bin/env python3
"""
Script: fetch_bridges.py
Description: Automatically fetches obfs4 bridges from the Tor BridgeDB API
             and injects them into the AnonSurf torrc configuration file.
"""

import requests
import os
import sys
import shutil
from datetime import datetime

# Configuration
TORRC_PATH = "/etc/anonsurf/torrc"
MOAT_API_URL = "https://bridges.torproject.org/moat/circumvention/request"

def fetch_bridges():
    """Fetches obfs4 bridges from the Tor Project MOAT API."""
    print("[*] Requesting new obfs4 bridges from Tor BridgeDB...")
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64)"
    }
    
    # Standard payload to request obfs4 bridges
    payload = {
        "data": [
            {
                "version": "0.1.0",
                "type": "client-transports",
                "supported": ["obfs4"]
            }
        ]
    }

    try:
        response = requests.post(MOAT_API_URL, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        bridges = data.get("data", {}).get("bridges", [])
        return bridges
        
    except requests.exceptions.ConnectionError:
        print("\n[!] Connection Error: The Tor BridgeDB API is blocked by your ISP.")
        print("[!] This is common in highly censored regions (e.g., Myanmar).")
        print("[*] FALLBACK REQUIRED: Please use the Telegram bot (@GetBridgesBot)")
        print("    to fetch obfs4 bridges and manually inject them into /etc/anonsurf/torrc.")
        return []
    except Exception as e:
        print(f"\n[!] API Request Failed: {e}")
        print("[!] Note: The Tor API sometimes rate-limits. Try again in 5 minutes.")
        return []

def update_torrc(bridges):
    """Backs up the old torrc and injects the new bridges."""
    print("[*] Updating torrc configuration...")
    
    if not os.path.exists(TORRC_PATH):
        print(f"[!] Error: {TORRC_PATH} does not exist. Is AnonSurf installed?")
        return False

    # 1. Create a timestamped backup
    backup_path = f"{TORRC_PATH}.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        shutil.copy2(TORRC_PATH, backup_path)
        print(f"[+] Backup created at: {backup_path}")
    except Exception as e:
        print(f"[!] Failed to create backup: {e}")
        return False

    # 2. Read existing config and remove old 'Bridge' lines
    try:
        with open(TORRC_PATH, 'r') as f:
            lines = f.readlines()
            
        new_lines = [line for line in lines if not line.strip().startswith("Bridge obfs4")]

        # 3. Ensure required Tor settings exist
        if not any(line.strip() == "UseBridges 1" for line in new_lines):
            new_lines.append("UseBridges 1\n")
        if not any("ClientTransportPlugin obfs4" in line for line in new_lines):
            new_lines.append("ClientTransportPlugin obfs4 exec /usr/bin/obfs4proxy\n")

        # 4. Append the newly fetched bridges
        for bridge in bridges:
            new_lines.append(f"Bridge {bridge}\n")

        # 5. Write back to the file
        with open(TORRC_PATH, 'w') as f:
            f.writelines(new_lines)
            
        print(f"[+] Successfully injected {len(bridges)} new bridges into torrc.")
        return True
        
    except Exception as e:
        print(f"[!] Failed to update torrc: {e}")
        return False

def main():
    # Ensure script is run with sudo
    if os.geteuid() != 0:
        print("[!] Please run this script with sudo: sudo python3 fetch_bridges.py")
        sys.exit(1)

    bridges = fetch_bridges()
    
    if bridges:
        print(f"[+] Fetched {len(bridges)} bridges successfully.")
        if update_torrc(bridges):
            print("\n[✓] Configuration updated. To apply changes, restart AnonSurf:")
            print("    sudo ~/tor-obfs4-dpi-bypass/scripts/anonsurf-toggle.sh stop")
            print("    sudo ~/tor-obfs4-dpi-bypass/scripts/anonsurf-toggle.sh start")
    else:
        print("[!] No bridges were fetched. Configuration unchanged.")

if __name__ == "__main__":
    main()
