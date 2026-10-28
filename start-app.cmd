@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 run_app.py --port 8765
) else (
  python run_app.py --port 8765
)
if errorlevel 1 pause
