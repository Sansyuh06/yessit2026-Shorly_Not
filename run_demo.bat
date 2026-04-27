@echo off
echo ============================================
echo   FinQuantum Shield — Demo Launcher
echo ============================================
echo.

REM Check Qiskit
python -c "import qiskit, qiskit_aer" 2>nul || (
    echo ERROR: Qiskit not installed.
    echo Run: pip install qiskit qiskit-aer
    pause
    exit /b 1
)

echo Starting KMS Server...
start "KMS Server [Window 1]" cmd /k "cd /d %~dp0 && python -m uvicorn kms.kms_server:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo Starting CMD Logger...
start "CMD Event Logger [Window 2]" cmd /k "cd /d %~dp0 && python logger\cmd_logger.py"

timeout /t 1 /nobreak >nul

echo Starting Streamlit Dashboard...
start "SOC Dashboard [Window 3]" cmd /k "cd /d %~dp0 && streamlit run dashboard\dashboard_ui.py --server.port 8501"

timeout /t 2 /nobreak >nul

echo Starting Attacker Console...
start "Attacker Console [Window 4]" cmd /k "cd /d %~dp0 && python attacker_console.py"

timeout /t 2 /nobreak >nul

echo Opening Banking Web App...
start http://localhost:8000/app

echo.
echo ============================================
echo   All windows launched!
echo.
echo   Bank Web UI:      http://localhost:8000/app
echo   KMS API:          http://localhost:8000
echo   API Docs:         http://localhost:8000/docs
echo   SOC Dashboard:    http://localhost:8501
echo.
echo   DEMO SEQUENCE:
echo   1. Open http://localhost:8000/app in browser
echo   2. Send a transfer — watch CMD Logger
echo   3. Hand Attacker Console to judge
echo   4. Judge presses [3] Multi-Path Compromise
echo   5. Try to send another transfer — watch it BLOCK
echo   6. Watch escalation cascade in all windows
echo   7. Judge presses [4] Reset — system recovers
echo ============================================
pause
