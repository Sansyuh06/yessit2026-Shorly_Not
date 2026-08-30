@echo off
TITLE ShorlyNot - Quantum Security Framework & Bank Demo
echo ======================================================================
echo           SHORLYNOT - SIH 2026 PS 26141 DEMO LAUNCHER
echo   Quantum Digital Signatures (ShorlyNot-QDS-T1) ^& Q-STDF Threat Engine
echo ======================================================================
echo.

echo [*] Installing skeleton package in editable mode...
pip install -e skeleton --quiet

echo [*] Starting ShorlyNot Skeleton API on port 8000 in background...
start "ShorlyNot Skeleton API (:8000)" cmd /k "cd skeleton && uvicorn shorlynot_skeleton.api.app:app --host 127.0.0.1 --port 8000"

timeout /t 2 /nobreak >nul

echo [*] Starting ShorlyNot Mock Bank & SOC on port 8080...
start "ShorlyNot Bank Portal & SOC (:8080)" cmd /k "python -m bank.app.main"

timeout /t 2 /nobreak >nul

echo.
echo ======================================================================
echo   Demo services started successfully!
echo   ------------------------------------------------------------------
echo   - Bank Customer Web Portal: http://127.0.0.1:8080 (Alice / alice123)
echo   - Dark SOC Threat Center:   http://127.0.0.1:8080/soc
echo   - Skeleton OpenAPI Swagger: http://127.0.0.1:8000/docs
echo ======================================================================
echo.
pause
