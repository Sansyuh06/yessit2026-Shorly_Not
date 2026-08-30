#!/bin/sh
# Deploy quantum firmware scripts to OpenWrt router
# Usage: sh deploy.sh [router_ip]

ROUTER="${1:-192.168.1.1}"
DIR="$(dirname "$0")"

echo "=== Deploying Quantum Firmware to $ROUTER ==="

scp "$DIR/scripts/qberd" "$DIR/scripts/ledctl" "$DIR/scripts/lockdownctl" root@${ROUTER}:/usr/bin/
scp "$DIR/config/quantum" root@${ROUTER}:/etc/config/
scp "$DIR/init/qberd" root@${ROUTER}:/etc/init.d/
scp "$DIR/button/wps" root@${ROUTER}:/etc/rc.button/

ssh root@${ROUTER} "mkdir -p /etc/hotplug.d/usb"
scp "$DIR/hotplug/20-quantum-usb" root@${ROUTER}:/etc/hotplug.d/usb/

ssh root@${ROUTER} "chmod +x /usr/bin/qberd /usr/bin/ledctl /usr/bin/lockdownctl /etc/init.d/qberd /etc/rc.button/wps /etc/hotplug.d/usb/20-quantum-usb"
ssh root@${ROUTER} "/etc/init.d/qberd enable && /etc/init.d/qberd start"

echo "=== Done! qberd is running on $ROUTER ==="
