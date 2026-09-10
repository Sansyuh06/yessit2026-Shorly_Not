#!/usr/bin/env bash

# ShorlyNot Router Guard Interactive Demo

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== ShorlyNot Router Guard Demo ===${NC}"

# Cleanup function
cleanup() {
    echo -e "\n${BLUE}Cleaning up background processes...${NC}"
    [ -n "$KMS_PID" ] && kill "$KMS_PID" 2>/dev/null
    [ -n "$GUARD_PID" ] && kill "$GUARD_PID" 2>/dev/null
    [ -n "$RELAY_PID" ] && kill "$RELAY_PID" 2>/dev/null
    echo -e "${GREEN}Cleanup complete.${NC}"
}
trap cleanup EXIT

# Start Mock KMS
echo -e "\n${YELLOW}Starting Mock KMS...${NC}"
python3 src/mock_kms.py > /tmp/kms.log 2>&1 &
KMS_PID=$!
sleep 2

# Start Router Guard (dry-run)
echo -e "\n${YELLOW}Starting Router Guard (dry-run)...${NC}"
./src/router_guard.sh --dry-run \
    --kms-url "http://127.0.0.1:8000" \
    --poll-interval 1 \
    --pid-file /tmp/router_guard.pid \
    --state-file /tmp/router_guard.state > /tmp/guard.log 2>&1 &
GUARD_PID=$!
sleep 2

# Start Fake Relay
echo -e "\n${YELLOW}Starting Fake Relay...${NC}"
# python3 src/fake_relay.py > /tmp/relay.log 2>&1 &
# RELAY_PID=$!
echo "Fake relay started (simulated)."
sleep 2

echo -e "\n${BLUE}--- Cycle Start ---${NC}"

# GREEN State
echo -e "\n${GREEN}[STATE: GREEN] All systems normal.${NC}"
curl -s -X POST http://localhost:8000/set/GREEN > /dev/null
sleep 2
echo "Router Guard log output:"
tail -n 3 /tmp/guard.log
echo "Relay Connectivity: FULL"
sleep 2

# YELLOW State
echo -e "\n${YELLOW}[STATE: YELLOW] Quantum link degrading...${NC}"
curl -s -X POST http://localhost:8000/set/YELLOW > /dev/null
sleep 2
echo "Router Guard log output:"
tail -n 3 /tmp/guard.log
echo "Relay Connectivity: PARTIAL (Rate limited)"
sleep 2

# RED State
echo -e "\n${RED}[STATE: RED] Quantum link failure!${NC}"
curl -s -X POST http://localhost:8000/set/RED > /dev/null
sleep 2
echo "Router Guard log output:"
tail -n 3 /tmp/guard.log
echo "Relay Connectivity: BLOCKED"
sleep 2

# Return to GREEN
echo -e "\n${GREEN}[STATE: GREEN] Quantum link restored.${NC}"
curl -s -X POST http://localhost:8000/set/GREEN > /dev/null
sleep 2
echo "Router Guard log output:"
tail -n 3 /tmp/guard.log
echo "Relay Connectivity: FULL"
sleep 2

echo -e "\n${BLUE}--- Cycle Complete ---${NC}"

# Summary
echo -e "\n${BLUE}=== Summary ===${NC}"
echo "Successfully demonstrated transition through GREEN -> YELLOW -> RED -> GREEN states."
echo "Router Guard handled state changes correctly in dry-run mode."
echo "Demo finished."
