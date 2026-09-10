.PHONY: help test test-verbose lint mock-kms guard guard-live relay clean firmware check-deps demo

# Default target
help:
	@echo "ShorlyNot Router Guard Makefile"
	@echo "Available targets:"
	@echo "  help         - list all targets with descriptions (default)"
	@echo "  test         - run all tests"
	@echo "  test-verbose - run tests with verbose output"
	@echo "  lint         - run shellcheck on shell scripts"
	@echo "  mock-kms     - start the mock KMS server"
	@echo "  guard        - start router_guard in dry-run mode"
	@echo "  guard-live   - start router_guard (requires root for nftables)"
	@echo "  relay        - start the fake relay server"
	@echo "  clean        - cleanup temp files"
	@echo "  firmware     - build OpenWrt firmware image"
	@echo "  check-deps   - verify required dependencies are installed"
	@echo "  demo         - run a full demo (start KMS, guard in dry-run, cycle through states)"

test:
	@echo "Running tests..."
	@bash ./tests/run_tests.sh

test-verbose:
	@echo "Running tests verbosely..."
	@bash ./tests/run_tests.sh --verbose

lint:
	@echo "Running shellcheck..."
	@shellcheck src/router_guard.sh tools/demo.sh || echo "Shellcheck issues found or shellcheck not installed"

mock-kms:
	@echo "Starting Mock KMS server..."
	python3 src/mock_kms.py

guard:
	@echo "Starting Router Guard (dry-run)..."
	./src/router_guard.sh --dry-run

guard-live:
	@echo "Starting Router Guard (LIVE)..."
	@if [ "$$(id -u)" != "0" ]; then echo "Requires root for firewall"; exit 1; fi
	./src/router_guard.sh

relay:
	@echo "Starting fake relay..."
	python3 src/fake_relay.py

clean:
	@echo "Cleaning up temp files..."
	rm -rf __pycache__ *.pyc .pytest_cache

firmware:
	@echo "Building OpenWrt firmware image..."
	bash openwrt/build_image.sh

check-deps:
	@echo "Checking dependencies..."
	@command -v python3 >/dev/null 2>&1 || { echo >&2 "python3 required but not installed. Aborting."; exit 1; }
	@command -v curl >/dev/null 2>&1 || { echo >&2 "curl required but not installed. Aborting."; exit 1; }
	@command -v nft >/dev/null 2>&1 || { echo >&2 "nftables (nft) required but not installed. Aborting."; exit 1; }
	@echo "All dependencies met."

demo:
	@echo "Running full demo..."
	./tools/demo.sh
