#!/bin/bash
# Test KMS unavailability handling
source "$(dirname "${BASH_SOURCE[0]}")/test_framework.sh"

PORT=18005

echo -e "\n${BOLD}=== test_kms_failure.sh ===${NC}"

# T1: KMS unreachable from start — guard doesn't crash
echo "T1: KMS unreachable — guard survives"
setup
# Don't start KMS — guard should handle gracefully
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765
wait_for_poll 3
# Verify the guard process is still alive
alive=0
for pid in "${PIDS_TO_KILL[@]}"; do
    kill -0 "$pid" 2>/dev/null && alive=1
done
assert_equals "1" "$alive" "Guard process still running despite unreachable KMS"
teardown

# T2: KMS goes down after GREEN
echo "T2: KMS goes down after GREEN"
setup
start_mock_kms $PORT "GREEN"
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765
wait_for_poll 3
# Kill the KMS
kill "${PIDS_TO_KILL[0]}" 2>/dev/null
wait "${PIDS_TO_KILL[0]}" 2>/dev/null
wait_for_poll 3
# Guard should still be running
guard_alive=0
kill -0 "${PIDS_TO_KILL[1]}" 2>/dev/null && guard_alive=1
assert_equals "1" "$guard_alive" "Guard survives KMS going down"
assert_file_contains "$MOCK_DIR/guard.log" "unreachable" "Guard logs KMS failure"
teardown

# T3: After MAX_FAILURES, guard blocks port (fail-safe)
echo "T3: Fail-safe block after MAX_FAILURES"
setup
# No KMS started, max-failures=3, poll every 1s → should block after ~3s
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765 --max-failures 3
wait_for_poll 6
assert_file_contains "$IPTABLES_RULES" "DROP" "Port blocked after 3 consecutive failures"
teardown

# T4: KMS comes back — guard recovers
echo "T4: Guard recovers when KMS comes back"
setup
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765 --max-failures 3
wait_for_poll 6
assert_file_contains "$IPTABLES_RULES" "DROP" "Initially blocked (fail-safe)"
# Now start the KMS
start_mock_kms $PORT "GREEN"
wait_for_poll 3
assert_file_not_contains "$IPTABLES_RULES" "DROP" "Unblocked after KMS returns GREEN"
teardown

print_summary
exit $?
