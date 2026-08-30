#!/usr/bin/env bash
# ShorlyNot SIH 2026 PS 26141 Demo Launcher
set -e

echo "======================================================================"
echo "          SHORLYNOT - SIH 2026 PS 26141 DEMO LAUNCHER"
echo "  Quantum Digital Signatures (ShorlyNot-QDS-T1) & Q-STDF Threat Engine"
echo "======================================================================"

HOST="${HOST:-0.0.0.0}"

echo "[*] Installing dependencies and skeleton package..."
pip install -r requirements.txt -e skeleton --quiet

echo "[*] Launching ShorlyNot Skeleton API on $HOST:8000..."
uvicorn shorlynot_skeleton.api.app:app --host "$HOST" --port 8000 &
SKELETON_PID=$!

sleep 2

echo "[*] Launching ShorlyNot Bank & SOC on $HOST:8080..."
uvicorn bank.app.main:app --host "$HOST" --port 8080 &
BANK_PID=$!

sleep 2

echo "[*] Running smoke health check..."
python scripts/smoke_check.py

echo ""
echo "======================================================================"
echo "  Demo services are now live:"
echo "  - Bank Customer Portal: http://127.0.0.1:8080 (Alice / alice123)"
echo "  - Dark SOC Threat Radar: http://127.0.0.1:8080/soc"
echo "  - Skeleton OpenAPI Docs: http://127.0.0.1:8000/docs"
echo "======================================================================"
echo "Press Ctrl+C to terminate both services."

trap "kill $SKELETON_PID $BANK_PID 2>/dev/null || true" EXIT
wait
