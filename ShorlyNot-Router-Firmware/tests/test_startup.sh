#!/bin/bash
# Test startup / shutdown behavior
source "$(dirname "${BASH_SOURCE[0]}")/test_framework.sh"

PORT=18007

echo -e "\n${BOLD}=== test_startup.sh ===${NC}"

# T1: Guard cleans stale rules on startup
echo "T1: Stale rule cleanup on startup"
setup
# Pre-inject a stale DROP rule (same format as mock nft stores)
echo "tcp dport 8765 drop" > "$IPTABLES_RULES"
start_mock_kms $PORT "GREEN"
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765
wait_for_poll 3
assert_file_not_contains "$IPTABLES_RULES" "DROP" "Stale DROP rule cleaned on startup"
teardown

# T2: Guard writes PID file
echo "T2: PID file creation"
setup
start_mock_kms $PORT "GREEN"
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765
wait_for_poll 2
pid_exists=$([ -f "$MOCK_DIR/guard.pid" ] && echo "1" || echo "0")
assert_equals "1" "$pid_exists" "PID file created"
if [ -f "$MOCK_DIR/guard.pid" ]; then
    pid_content=$(cat "$MOCK_DIR/guard.pid")
    pid_valid=$([ -n "$pid_content" ] && echo "1" || echo "0")
    assert_equals "1" "$pid_valid" "PID file contains a PID"
fi
teardown

# T3: Guard writes state file
echo "T3: State file creation"
setup
start_mock_kms $PORT "GREEN"
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765
wait_for_poll 3
state_exists=$([ -f "$MOCK_DIR/guard.state" ] && echo "1" || echo "0")
assert_equals "1" "$state_exists" "State file created"
if [ -f "$MOCK_DIR/guard.state" ]; then
    state_content=$(cat "$MOCK_DIR/guard.state")
    assert_equals "GREEN" "$state_content" "State file shows GREEN"
fi
teardown

# T4: Clean shutdown (SIGTERM) removes DROP rule
echo "T4: Clean shutdown removes DROP rule"
setup
start_mock_kms $PORT "RED"
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765
wait_for_poll 3
assert_file_contains "$IPTABLES_RULES" "DROP" "DROP rule present under RED"
# Send SIGTERM (graceful shutdown)
guard_pid="${PIDS_TO_KILL[1]}"
kill -TERM "$guard_pid" 2>/dev/null
wait_for_poll 2
assert_file_not_contains "$IPTABLES_RULES" "DROP" "DROP rule removed on clean shutdown"
teardown

# T5: Guard can restart cleanly after ungraceful kill
echo "T5: Restart after crash"
setup
start_mock_kms $PORT "RED"
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765
wait_for_poll 3
assert_file_contains "$IPTABLES_RULES" "DROP" "First run: DROP present"
# Kill ungracefully (stale rule remains)
kill -9 "${PIDS_TO_KILL[1]}" 2>/dev/null
wait "${PIDS_TO_KILL[1]}" 2>/dev/null
# Restart — the new instance should clean stale rules then re-add
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765
wait_for_poll 3
num_drops=$(count_in_file "$IPTABLES_RULES" "DROP")
assert_equals "1" "$num_drops" "After restart: exactly one DROP rule"
teardown

print_summary
exit $?
