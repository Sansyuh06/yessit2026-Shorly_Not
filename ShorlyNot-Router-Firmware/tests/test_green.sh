#!/bin/bash
# Test GREEN status behavior
source "$(dirname "${BASH_SOURCE[0]}")/test_framework.sh"

PORT=18001

echo -e "\n${BOLD}=== test_green.sh ===${NC}"

# T1: Guard starts with GREEN KMS, no DROP rule inserted
echo "T1: GREEN status — no DROP rule"
setup
start_mock_kms $PORT "GREEN"
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765
wait_for_poll 3
assert_file_not_contains "$IPTABLES_RULES" "DROP" "No DROP rule when KMS is GREEN"
teardown

# T2: Relay port remains accessible under GREEN
echo "T2: GREEN status — relay port not blocked"
setup
start_mock_kms $PORT "GREEN"
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765
wait_for_poll 3
assert_file_not_contains "$IPTABLES_RULES" "8765" "Port 8765 not mentioned in rules"
teardown

# T3: Multiple GREEN polls don't create spurious firewall operations
echo "T3: Multiple GREEN polls — no spurious rules"
setup
start_mock_kms $PORT "GREEN"
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765
wait_for_poll 5
# Check that no rule additions were logged after initial cleanup
insert_count=$(count_in_file "$FW_LOG" "add rule")
assert_equals "0" "$insert_count" "No insert operations under sustained GREEN"
teardown

print_summary
exit $?
