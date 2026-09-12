@echo off
TITLE ShorlyNot - Quantum Security Framework & Bank Demo
echo ======================================================================
echo           SHORLYNOT - SIH 2026 PS 26141 DEMO LAUNCHER
echo   Quantum Digital Signatures (ShorlyNot-QDS-T1) ^& Q-STDF Threat Engine
echo ======================================================================
echo.

set HOST=0.0.0.0
set SHORLYNOT_REQUIRE_API=1
if "%KMS_PORT%"=="" set KMS_PORT=8000
if "%SKELETON_PORT%"=="" set SKELETON_PORT=8001
if "%BANK_PORT%"=="" set BANK_PORT=8081
set KMS_URL=http://127.0.0.1:%KMS_PORT%
set SHORLYNOT_API_URL=http://127.0.0.1:%SKELETON_PORT%
set SHORLYNOT_BANK_URL=http://127.0.0.1:%BANK_PORT%

echo [*] Installing dependencies and skeleton package...
pip install -r requirements.txt -e skeleton --quiet

echo [*] Checking Router QKD KMS on %HOST%:%KMS_PORT%...
python -c "import httpx, sys; sys.exit(0 if httpx.get('http://127.0.0.1:%KMS_PORT%/link_status', timeout=1.0).status_code == 200 else 1)" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [*] Starting ShorlyNot Router QKD KMS on %HOST%:%KMS_PORT%...
    start "ShorlyNot Router Guard KMS (:%KMS_PORT%)" cmd /k "python ShorlyNot-Router-Firmware\src\mock_kms.py --port %KMS_PORT%"
    timeout /t 2 /nobreak >nul
) else (
    echo [+] Router QKD KMS is already running on port %KMS_PORT%.
)

echo [*] Starting ShorlyNot Skeleton API on %HOST%:%SKELETON_PORT% in background...
start "ShorlyNot Skeleton API (:%SKELETON_PORT%)" cmd /k "cd skeleton && python -m uvicorn shorlynot_skeleton.api.app:app --host %HOST% --port %SKELETON_PORT%"

timeout /t 3 /nobreak >nul

echo [*] Starting ShorlyNot Mock Bank & SOC on %HOST%:%BANK_PORT% (Strict API Enforcement Active)...
start "ShorlyNot Bank Portal & SOC (:%BANK_PORT%)" cmd /k "python -m uvicorn bank.app.main:app --host %HOST% --port %BANK_PORT%"

timeout /t 3 /nobreak >nul

echo [*] Running smoke verification across all 3 tiers...
python scripts\smoke_check.py %KMS_URL% %SHORLYNOT_API_URL% %SHORLYNOT_BANK_URL%

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Demo startup failed smoke check!
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo   All 3 ShorlyNot Demo Services are Live:
echo   ------------------------------------------------------------------
echo   - OpenWrt Router Guard KMS: http://127.0.0.1:%KMS_PORT%
echo   - Bank Customer Web Portal: http://127.0.0.1:%BANK_PORT% (Alice / alice123)
echo   - Dark SOC Radar Console:   http://127.0.0.1:%BANK_PORT%/soc (ops / ops123)
echo   - Skeleton OpenAPI Swagger: http://127.0.0.1:%SKELETON_PORT%/docs
echo ======================================================================
echo.
pause
