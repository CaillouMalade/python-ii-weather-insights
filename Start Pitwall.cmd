@echo off
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 (
  echo Pitwall needs Node.js 22.13 or newer from https://nodejs.org/en/download
  pause
  exit /b 1
)
if not exist node_modules\.bin\vite.cmd (
  call npm ci
  if errorlevel 1 exit /b 1
)
call npm start -- --open
if errorlevel 1 pause
