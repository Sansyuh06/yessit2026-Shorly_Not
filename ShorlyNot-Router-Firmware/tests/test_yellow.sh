#!/bin/bash
# Test YELLOW status behavior
source "$(dirname "${BASH_SOURCE[0]}")/test_framework.sh"

PORT=18002

echo -e "\n${BOLD}=== test_yellow.sh ===${NC}"

# T1: YELLOW does NOT block (paper says YELLOW still issues a key)
echo "T1: YELLOW status — no DROP rule"
setup
start_mock_kms $PORT "YELLOW"
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765
wait_for_poll 3
assert_file_not_contains "$IPTABLES_RULES" "DROP" "No DROP rule when KMS is YELLOW"
teardown

# T2: GREEN → YELLOW — no firewall change
echo "T2: GREEN→YELLOW transition — no firewall change"
setup
start_mock_kms $PORT "GREEN"
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765
wait_for_poll 3
set_kms_status $PORT "YELLOW"
wait_for_poll 3
assert_file_not_contains "$IPTABLES_RULES" "DROP" "No DROP rule after GREEN→YELLOW"
teardown

print_summary
exit $?
