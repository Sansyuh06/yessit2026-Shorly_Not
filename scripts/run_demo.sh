#!/usr/bin/env bash
# ShorlyNot SIH 2026 PS 26141 Demo Launcher
set -e

echo "======================================================================"
echo "          SHORLYNOT - SIH 2026 PS 26141 DEMO LAUNCHER"
echo "  Quantum Digital Signatures (ShorlyNot-QDS-T1) & Q-STDF Threat Engine"
echo "======================================================================"

echo "[*] Installing skeleton package in editable mode..."
pip install -e skeleton --quiet

echo "[*] Launching ShorlyNot Skeleton API on port 8000..."
uvicorn shorlynot_skeleton.api.app:app --host 127.0.0.1 --port 8000 &
SKELETON_PID=$!

sleep 2

echo "[*] Launching ShorlyNot Bank & SOC on port 8080..."
python -m bank.app.main &
BANK_PID=$!

echo ""
echo "======================================================================"
echo "  Demo services are now live:"
echo "  - Bank Customer Portal: http://127.0.0.1:8080 (Alice / alice123)"
echo "  - Dark SOC Threat Radar: http://127.0.0.1:8080/soc"
echo "  - Skeleton OpenAPI Docs: http://127.0.0.1:8000/docs"
echo "======================================================================"
echo "Press Ctrl+C to terminate both services."

trap "kill $SKELETON_PID $BANK_PID" EXIT
wait
