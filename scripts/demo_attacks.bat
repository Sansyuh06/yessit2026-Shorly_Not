@echo off
REM ShorlyNot SIH 2026 PS 26141 One-Shot Attack Demonstration Runner (Windows)
echo [*] Executing ShorlyNot One-Shot Attack & Defense Demonstration...
python scripts\demo_attacks.py %*
if %ERRORLEVEL% NEQ 0 (
    echo [-] Attack demonstration failed with error code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
