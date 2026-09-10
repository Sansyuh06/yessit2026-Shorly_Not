#!/bin/bash
# Test state transitions
source "$(dirname "${BASH_SOURCE[0]}")/test_framework.sh"

PORT=18004

echo -e "\n${BOLD}=== test_transitions.sh ===${NC}"

# T1: GREEN → RED — DROP rule appears
echo "T1: GREEN→RED — DROP rule appears"
setup
start_mock_kms $PORT "GREEN"
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765
wait_for_poll 3
assert_file_not_contains "$IPTABLES_RULES" "DROP" "Initially no DROP"
set_kms_status $PORT "RED"
wait_for_poll 3
assert_file_contains "$IPTABLES_RULES" "DROP" "DROP appears after RED"
teardown

# T2: RED → GREEN — DROP rule removed
echo "T2: RED→GREEN — DROP rule removed"
setup
start_mock_kms $PORT "RED"
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765
wait_for_poll 3
assert_file_contains "$IPTABLES_RULES" "DROP" "Initially DROP present"
set_kms_status $PORT "GREEN"
wait_for_poll 3
assert_file_not_contains "$IPTABLES_RULES" "DROP" "DROP removed after GREEN"
teardown

# T3: GREEN → YELLOW → RED → GREEN — full cycle
echo "T3: Full cycle GREEN→YELLOW→RED→GREEN"
setup
start_mock_kms $PORT "GREEN"
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765
wait_for_poll 3
assert_file_not_contains "$IPTABLES_RULES" "DROP" "GREEN: no block"

set_kms_status $PORT "YELLOW"
wait_for_poll 3
assert_file_not_contains "$IPTABLES_RULES" "DROP" "YELLOW: still no block"

set_kms_status $PORT "RED"
wait_for_poll 3
assert_file_contains "$IPTABLES_RULES" "DROP" "RED: blocked"

set_kms_status $PORT "GREEN"
wait_for_poll 3
assert_file_not_contains "$IPTABLES_RULES" "DROP" "Back to GREEN: unblocked"
teardown

# T4: RED → YELLOW → GREEN — recovery path
echo "T4: Recovery path RED→YELLOW→GREEN"
setup
start_mock_kms $PORT "RED"
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765
wait_for_poll 3
assert_file_contains "$IPTABLES_RULES" "DROP" "Initial RED"

set_kms_status $PORT "YELLOW"
wait_for_poll 3
assert_file_not_contains "$IPTABLES_RULES" "DROP" "YELLOW clears block"

set_kms_status $PORT "GREEN"
wait_for_poll 3
assert_file_not_contains "$IPTABLES_RULES" "DROP" "GREEN stays clear"
teardown

# T5: Rapid transitions
echo "T5: Rapid GREEN→RED→GREEN"
setup
start_mock_kms $PORT "GREEN"
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765
wait_for_poll 2
set_kms_status $PORT "RED"
wait_for_poll 3
assert_file_contains "$IPTABLES_RULES" "DROP" "Rapid RED applied"
set_kms_status $PORT "GREEN"
wait_for_poll 3
assert_file_not_contains "$IPTABLES_RULES" "DROP" "Rapid GREEN restored"
teardown

print_summary
exit $?
