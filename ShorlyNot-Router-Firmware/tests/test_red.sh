#!/bin/bash
# Test RED status behavior
source "$(dirname "${BASH_SOURCE[0]}")/test_framework.sh"

PORT=18003

echo -e "\n${BOLD}=== test_red.sh ===${NC}"

# T1: RED inserts DROP rule
echo "T1: RED status — DROP rule inserted"
setup
start_mock_kms $PORT "RED"
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765
wait_for_poll 3
assert_file_contains "$IPTABLES_RULES" "DROP" "DROP rule present when KMS is RED"
teardown

# T2: Multiple RED polls — only one DROP rule (idempotency)
echo "T2: Sustained RED — no duplicate DROP rules"
setup
start_mock_kms $PORT "RED"
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765
wait_for_poll 5
num_drops=$(count_in_file "$IPTABLES_RULES" "DROP")
assert_equals "1" "$num_drops" "Exactly one DROP rule after multiple RED polls"
teardown

# T3: DROP rule targets the correct port
echo "T3: DROP rule targets correct port"
setup
start_mock_kms $PORT "RED"
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765
wait_for_poll 3
assert_file_contains "$IPTABLES_RULES" "8765" "DROP rule references port 8765"
teardown

print_summary
exit $?
