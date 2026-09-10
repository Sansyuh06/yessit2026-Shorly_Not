#!/bin/bash
# Test malformed/bad KMS responses
source "$(dirname "${BASH_SOURCE[0]}")/test_framework.sh"

PORT=18006

echo -e "\n${BOLD}=== test_malformed.sh ===${NC}"

# Helper: start a minimal HTTP server that returns a fixed response body
start_bad_server() {
    local port="$1"
    local status_code="$2"
    local body="$3"
    python3 -c "
import http.server, sys

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response($status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'''$body''')
    def log_message(self, *a): pass

http.server.HTTPServer(('', $port), H).serve_forever()
" > "$MOCK_DIR/bad_server.log" 2>&1 &
    PIDS_TO_KILL+=($!)
    sleep 1
}

# T1: Empty body → treated as failure
echo "T1: Empty response body"
setup
start_bad_server $PORT 200 ""
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765 --max-failures 3
wait_for_poll 6
assert_file_contains "$IPTABLES_RULES" "DROP" "Empty body triggers fail-safe block"
teardown

# T2: Invalid JSON → treated as failure
echo "T2: Invalid JSON response"
setup
start_bad_server $PORT 200 '{not valid json!!!'
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765 --max-failures 3
wait_for_poll 6
assert_file_contains "$IPTABLES_RULES" "DROP" "Invalid JSON triggers fail-safe block"
teardown

# T3: Valid JSON, unknown status value
echo "T3: Unknown status value"
setup
start_bad_server $PORT 200 '{"status": "PURPLE"}'
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765 --max-failures 3
wait_for_poll 6
assert_file_contains "$IPTABLES_RULES" "DROP" "Unknown status triggers fail-safe block"
teardown

# T4: HTTP 500 → treated as failure
echo "T4: HTTP 500 error"
setup
start_bad_server $PORT 500 '{"error": "internal"}'
start_guard "http://127.0.0.1:$PORT" --poll-interval 1 --relay-port 8765 --max-failures 3
wait_for_poll 6
assert_file_contains "$IPTABLES_RULES" "DROP" "HTTP 500 triggers fail-safe block"
teardown

print_summary
exit $?
