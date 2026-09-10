#!/bin/bash
# =============================================================================
# ShorlyNot Router Guard — Test Framework
# =============================================================================
# Lightweight test helpers: mock iptables, KMS control, assertions.
# Source this from each test_*.sh file.
# =============================================================================

# Colors
RED_C='\033[0;31m'
GREEN_C='\033[0;32m'
YELLOW_C='\033[0;33m'
BOLD='\033[1m'
NC='\033[0m'

# Counters
TEST_COUNT=0
PASS_COUNT=0
FAIL_COUNT=0

# Paths
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GUARD_SCRIPT="$PROJECT_ROOT/src/router_guard.sh"
KMS_SCRIPT="$PROJECT_ROOT/src/mock_kms.py"

# PIDs to clean up
PIDS_TO_KILL=()

# =============================================================================
# Setup / Teardown
# =============================================================================

setup() {
    export MOCK_DIR="$(mktemp -d)"
    export FW_LOG="$MOCK_DIR/fw.log"
    export FW_RULES="$MOCK_DIR/rules"
    export IPTABLES_LOG="$FW_LOG"
    export IPTABLES_RULES="$FW_RULES"
    export NFT_LOG="$FW_LOG"
    export NFT_RULES="$FW_RULES"
    touch "$FW_LOG" "$FW_RULES"

    # ---- Create mock nft -----------------------------------------------------
    cat > "$MOCK_DIR/nft" << 'MOCK_EOF'
#!/bin/bash
LOG="${NFT_LOG:-/tmp/nft.log}"
RULES="${NFT_RULES:-/tmp/rules}"

# Log the call
echo "$*" >> "$LOG"

case "$1" in
    add)
        shift # "add"
        case "$1" in
            rule)
                shift # "rule"
                echo "$*" >> "$RULES"
                exit 0
                ;;
            table|chain)
                exit 0
                ;;
        esac
        ;;
    flush)
        shift # "flush"
        case "$1" in
            chain)
                > "$RULES"
                exit 0
                ;;
        esac
        ;;
    list)
        cat "$RULES" 2>/dev/null
        exit 0
        ;;
    delete)
        > "$RULES"
        exit 0
        ;;
esac
exit 0
MOCK_EOF
    chmod +x "$MOCK_DIR/nft"

    # ---- Create mock iptables (fallback) -------------------------------------
    cat > "$MOCK_DIR/iptables" << 'MOCK_EOF'
#!/bin/bash
LOG="${IPTABLES_LOG:-/tmp/iptables.log}"
RULES="${IPTABLES_RULES:-/tmp/rules}"

echo "$*" >> "$LOG"

ACTION="$1"; shift
CHAIN="$1"; shift
RULE="$*"

case "$ACTION" in
    -C)
        grep -qxF -- "$RULE" "$RULES" 2>/dev/null
        exit $?
        ;;
    -I|-A)
        echo "$RULE" >> "$RULES"
        exit 0
        ;;
    -D)
        if ! grep -qxF -- "$RULE" "$RULES" 2>/dev/null; then
            exit 1
        fi
        TMPF="${RULES}.tmp"
        DELETED=0
        while IFS= read -r line || [ -n "$line" ]; do
            if [ "$DELETED" -eq 0 ] && [ "$line" = "$RULE" ]; then
                DELETED=1
            else
                echo "$line"
            fi
        done < "$RULES" > "$TMPF"
        mv -f "$TMPF" "$RULES"
        exit 0
        ;;
    -L)
        cat "$RULES" 2>/dev/null
        exit 0
        ;;
esac
exit 0
MOCK_EOF
    chmod +x "$MOCK_DIR/iptables"

    # Put mock first on PATH
    export PATH="$MOCK_DIR:$PATH"
}

teardown() {
    # Kill all tracked background processes
    for pid in "${PIDS_TO_KILL[@]}"; do
        kill "$pid" 2>/dev/null
        wait "$pid" 2>/dev/null
    done
    PIDS_TO_KILL=()

    # Remove temp dir
    [ -n "$MOCK_DIR" ] && rm -rf "$MOCK_DIR"
}

# =============================================================================
# KMS helpers
# =============================================================================

start_mock_kms() {
    local port="$1"
    local initial_status="${2:-GREEN}"
    python3 "$KMS_SCRIPT" --port "$port" --initial-status "$initial_status" \
        > "$MOCK_DIR/kms.log" 2>&1 &
    PIDS_TO_KILL+=($!)
    # Wait for KMS to be ready
    local tries=0
    while [ $tries -lt 30 ]; do
        if curl -sf "http://127.0.0.1:$port/health" >/dev/null 2>&1; then
            return 0
        fi
        sleep 0.2
        tries=$((tries + 1))
    done
    echo "WARNING: Mock KMS on port $port did not become ready"
    return 1
}

set_kms_status() {
    local port="$1"
    local status="$2"
    curl -sf "http://127.0.0.1:$port/set/$status" >/dev/null 2>&1
}

get_kms_status() {
    local port="$1"
    curl -sf "http://127.0.0.1:$port/link_status" 2>/dev/null
}

# =============================================================================
# Guard helpers
# =============================================================================

start_guard() {
    local kms_url="$1"
    shift
    # Run router_guard in background, pointing state/pid files to MOCK_DIR
    KMS_URL="$kms_url" \
    PID_FILE="$MOCK_DIR/guard.pid" \
    STATE_FILE="$MOCK_DIR/guard.state" \
    bash "$GUARD_SCRIPT" "$@" > "$MOCK_DIR/guard.log" 2>&1 &
    PIDS_TO_KILL+=($!)
    sleep 0.5  # Let it start and do initial cleanup
}

wait_for_poll() {
    local seconds="${1:-2}"
    sleep "$seconds"
}

# Count lines matching a pattern in a file (returns clean integer)
count_in_file() {
    local file="$1"
    local pattern="$2"
    local n
    n=$(grep -ci -- "$pattern" "$file" 2>/dev/null) || true
    # Strip any whitespace/CR
    echo "${n:-0}" | tr -cd '0-9'
}

# =============================================================================
# Assertions
# =============================================================================

assert_equals() {
    local expected="$1"
    local actual="$2"
    local msg="${3:-Expected '$expected', got '$actual'}"
    TEST_COUNT=$((TEST_COUNT + 1))
    if [ "$expected" = "$actual" ]; then
        echo -e "  ${GREEN_C}✓ PASS${NC}: $msg"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "  ${RED_C}✗ FAIL${NC}: $msg  (expected='$expected' actual='$actual')"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

assert_contains() {
    local haystack="$1"
    local needle="$2"
    local msg="${3:-String should contain '$needle'}"
    TEST_COUNT=$((TEST_COUNT + 1))
    if echo "$haystack" | grep -qi -- "$needle"; then
        echo -e "  ${GREEN_C}✓ PASS${NC}: $msg"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "  ${RED_C}✗ FAIL${NC}: $msg"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

assert_file_contains() {
    local file="$1"
    local pattern="$2"
    local msg="${3:-File $(basename "$file") should contain '$pattern'}"
    TEST_COUNT=$((TEST_COUNT + 1))
    if grep -qi -- "$pattern" "$file" 2>/dev/null; then
        echo -e "  ${GREEN_C}✓ PASS${NC}: $msg"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "  ${RED_C}✗ FAIL${NC}: $msg"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

assert_file_not_contains() {
    local file="$1"
    local pattern="$2"
    local msg="${3:-File $(basename "$file") should NOT contain '$pattern'}"
    TEST_COUNT=$((TEST_COUNT + 1))
    if ! grep -qi -- "$pattern" "$file" 2>/dev/null; then
        echo -e "  ${GREEN_C}✓ PASS${NC}: $msg"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "  ${RED_C}✗ FAIL${NC}: $msg"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

assert_exit_code() {
    local expected="$1"
    local actual="$2"
    local msg="${3:-Exit code should be $expected (got $actual)}"
    assert_equals "$expected" "$actual" "$msg"
}

# =============================================================================
# Summary (call at end of each test file)
# =============================================================================

print_summary() {
    echo ""
    echo -e "${BOLD}Results: $TEST_COUNT tests, ${GREEN_C}$PASS_COUNT passed${NC}, ${RED_C}$FAIL_COUNT failed${NC}"
    [ "$FAIL_COUNT" -gt 0 ] && return 1
    return 0
}
