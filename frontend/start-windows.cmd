@echo off
setlocal
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 (
  echo Node.js was not found. Install Node LTS, then reopen this file.
  echo https://nodejs.org/en/download/
  pause
  exit /b 1
)
where npm.cmd >nul 2>nul
if errorlevel 1 (
  echo npm was not found. Reinstall Node LTS and reopen your terminal.
  pause
  exit /b 1
)
if not exist node_modules\vite (
  echo Installing frontend dependencies. An internet connection is required.
  call npm.cmd install
  if errorlevel 1 (
    echo Installation failed. Keep the first error above for troubleshooting.
    pause
    exit /b 1
  )
)
echo Starting Aero Health. Open the Local address printed below.
call npm.cmd run dev
pause
