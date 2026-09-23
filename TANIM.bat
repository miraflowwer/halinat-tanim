@echo off
setlocal
cd /d "%~dp0"

echo Starting TANIM...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-tanim.ps1"

if errorlevel 1 (
  echo.
  echo TANIM did not start completely.
  echo Review the message above and .tanim\logs if they exist.
  echo.
  pause
  exit /b 1
)

exit /b 0
