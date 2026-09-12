#!/usr/bin/env bash
# ShorlyNot SIH 2026 PS 26141 Demo Launcher
set -e

echo "======================================================================"
echo "          SHORLYNOT - SIH 2026 PS 26141 DEMO LAUNCHER"
echo "  Quantum Digital Signatures (ShorlyNot-QDS-T1) & Q-STDF Threat Engine"
echo "======================================================================"

HOST="${HOST:-0.0.0.0}"
KMS_PORT="${KMS_PORT:-8000}"
SKELETON_PORT="${SKELETON_PORT:-8001}"
BANK_PORT="${BANK_PORT:-8081}"
export KMS_URL="http://127.0.0.1:${KMS_PORT}"
export SHORLYNOT_REQUIRE_API=1
export SHORLYNOT_API_URL="http://127.0.0.1:${SKELETON_PORT}"
export SHORLYNOT_BANK_URL="http://127.0.0.1:${BANK_PORT}"

echo "[*] Installing dependencies and skeleton package..."
pip install -r requirements.txt -e skeleton --quiet

# Launch Router KMS if not already running
if python -c "import httpx, sys; sys.exit(0 if httpx.get('http://127.0.0.1:${KMS_PORT}/link_status', timeout=1.0).status_code == 200 else 1)" 2>/dev/null; then
    echo "[+] Router QKD KMS is already active on port ${KMS_PORT}."
    KMS_PID=""
else
    echo "[*] Launching ShorlyNot Router QKD KMS on $HOST:${KMS_PORT}..."
    python ShorlyNot-Router-Firmware/src/mock_kms.py --port "${KMS_PORT}" &
    KMS_PID=$!
    sleep 2
fi

echo "[*] Launching ShorlyNot Skeleton API on $HOST:${SKELETON_PORT}..."
python -m uvicorn shorlynot_skeleton.api.app:app --host "$HOST" --port "${SKELETON_PORT}" &
SKELETON_PID=$!

sleep 2

echo "[*] Launching ShorlyNot Bank & SOC on $HOST:${BANK_PORT} (Strict API Enforcement Active)..."
python -m uvicorn bank.app.main:app --host "$HOST" --port "${BANK_PORT}" &
BANK_PID=$!

sleep 2

echo "[*] Running multi-tier smoke health check..."
python scripts/smoke_check.py "${KMS_URL}" "${SHORLYNOT_API_URL}" "${SHORLYNOT_BANK_URL}"

echo ""
echo "======================================================================"
echo "  All 3 ShorlyNot Demo Services are Live:"
echo "  - OpenWrt Router Guard KMS: http://127.0.0.1:${KMS_PORT}"
echo "  - Bank Customer Portal:     http://127.0.0.1:${BANK_PORT} (Alice / alice123)"
echo "  - Dark SOC Threat Radar:    http://127.0.0.1:${BANK_PORT}/soc (ops / ops123)"
echo "  - Skeleton OpenAPI Docs:    http://127.0.0.1:${SKELETON_PORT}/docs"
echo "======================================================================"
echo "Press Ctrl+C to terminate all services."

trap "kill $KMS_PID $SKELETON_PID $BANK_PID 2>/dev/null || true" EXIT
wait
