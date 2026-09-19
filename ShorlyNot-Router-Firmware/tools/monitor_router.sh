#!/usr/bin/env bash
# ==============================================================================
# ShorlyNot Router Guard - OpenWrt Live Telemetry Monitor
# Target: TP-Link Archer C6 v3.20 (MediaTek MT7621A / OpenWrt 22.03.7 fw4)
# ==============================================================================

ROUTER_IP="${ROUTER_IP:-192.168.1.1}"
INTERVAL="${INTERVAL:-1}"
CHAIN_NAME="${CHAIN_NAME:-router_guard_forward}"

echo "=== ShorlyNot Archer C6 Router Guard Telemetry Monitor ==="
echo "Target Router IP: ${ROUTER_IP}"
echo "Polling Interval: ${INTERVAL}s"
echo "Press [Ctrl+C] to stop."
echo "---------------------------------------------------------"

trap 'echo -e "\n[Monitor Stopped]"; exit 0' SIGINT SIGTERM

while true; do
  clear
  echo "=========================================================="
  echo "       SHORLYNOT ROUTER GUARD - ARCHER C6 CONSOLE         "
  echo "=========================================================="
  echo -n "Timestamp: "
  date "+%Y-%m-%d %H:%M:%S"
  echo -n "Guard State (/tmp/router_guard.state): "
  ssh -o StrictHostKeyChecking=no -o ConnectTimeout=2 "root@${ROUTER_IP}" "cat /tmp/router_guard.state 2>/dev/null || echo 'UNKNOWN/OFFLINE'"
  echo ""
  echo "--- Active NFTables Firewall Rules (inet fw4) ---"
  ssh -o StrictHostKeyChecking=no -o ConnectTimeout=2 "root@${ROUTER_IP}" "nft list chain inet fw4 ${CHAIN_NAME} 2>/dev/null || echo 'No active rules in chain'"
  echo "=========================================================="
  sleep "${INTERVAL}"
done
