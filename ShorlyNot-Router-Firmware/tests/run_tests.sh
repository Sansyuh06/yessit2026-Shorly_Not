#!/bin/bash
# =============================================================================
# ShorlyNot Router Guard — Test Runner
# =============================================================================
# Discovers and runs all test_*.sh files, reports summary.
#
# Usage:
#   ./run_tests.sh                  Run all tests
#   ./run_tests.sh --verbose        Show full output
#   ./run_tests.sh test_green.sh    Run a specific test
# =============================================================================

set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BOLD='\033[1m'
NC='\033[0m'

VERBOSE=0
TARGET_TEST=""

for arg in "$@"; do
    case "$arg" in
        --verbose|-v) VERBOSE=1 ;;
        test_*.sh)    TARGET_TEST="$arg" ;;
    esac
done

# ---- Check dependencies ----------------------------------------------------
echo -e "${BOLD}Checking dependencies...${NC}"
missing=0
for cmd in python3 curl bash grep sed; do
    if ! command -v "$cmd" &>/dev/null; then
        echo -e "  ${RED}✗${NC} $cmd not found"
        missing=1
    else
        echo -e "  ${GREEN}✓${NC} $cmd"
    fi
done

# Check jq (optional but preferred)
if command -v jq &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} jq (JSON parser)"
else
    echo -e "  ${YELLOW}~${NC} jq not found (will use grep fallback)"
fi

if [ "$missing" -eq 1 ]; then
    echo -e "${RED}Missing required dependencies. Aborting.${NC}"
    exit 1
fi

# ---- Discover tests ---------------------------------------------------------
cd "$SCRIPT_DIR"

if [ -n "$TARGET_TEST" ]; then
    if [ ! -f "$TARGET_TEST" ]; then
        echo -e "${RED}Test file not found: $TARGET_TEST${NC}"
        exit 1
    fi
    TEST_FILES=("$TARGET_TEST")
else
    TEST_FILES=()
    for f in test_*.sh; do
        [ "$f" = "test_framework.sh" ] && continue
        TEST_FILES+=("$f")
    done
fi

if [ ${#TEST_FILES[@]} -eq 0 ]; then
    echo -e "${YELLOW}No test files found.${NC}"
    exit 0
fi

echo ""
echo -e "${BOLD}Running ${#TEST_FILES[@]} test file(s)...${NC}"
echo "========================================"

TOTAL_PASSED=0
TOTAL_FAILED=0
FAILED_FILES=()

for test_file in "${TEST_FILES[@]}"; do
    chmod +x "$test_file" 2>/dev/null

    if [ $VERBOSE -eq 1 ]; then
        bash "./$test_file"
        exit_code=$?
    else
        output=$(bash "./$test_file" 2>&1)
        exit_code=$?
        # Show just the header and pass/fail lines
        echo "$output" | grep -E '===|✓ PASS|✗ FAIL|Results:'
    fi

    if [ $exit_code -ne 0 ]; then
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
        FAILED_FILES+=("$test_file")
    else
        TOTAL_PASSED=$((TOTAL_PASSED + 1))
    fi
done

# ---- Summary ----------------------------------------------------------------
echo ""
echo "========================================"
echo -e "${BOLD}Suite Summary${NC}"
echo -e "  Files run   : ${#TEST_FILES[@]}"
echo -e "  ${GREEN}Passed${NC}      : $TOTAL_PASSED"
echo -e "  ${RED}Failed${NC}      : $TOTAL_FAILED"

if [ ${#FAILED_FILES[@]} -gt 0 ]; then
    echo ""
    echo -e "${RED}Failed files:${NC}"
    for f in "${FAILED_FILES[@]}"; do
        echo "  - $f"
    done
fi

echo "========================================"

if [ $TOTAL_FAILED -gt 0 ]; then
    echo -e "${RED}${BOLD}TESTS FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}${BOLD}ALL TESTS PASSED${NC}"
    exit 0
fi
