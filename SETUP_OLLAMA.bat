@echo off
REM T10 AIRPS - Ollama One-Click Setup (Windows Batch)
REM This script automates everything

color 0F
title T10 AIRPS - Ollama Setup
cls

echo ================================================
echo T10 AIRPS - Ollama Fast Setup
echo ================================================
echo.

REM Check if PowerShell script exists
set PS_SCRIPT=%~dp0setup_ollama.ps1

REM Run PowerShell script
echo Running Ollama setup script...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "& '%PS_SCRIPT%'"

if errorlevel 1 (
    echo.
    echo ERROR: Setup failed!
    echo Please try manual installation: https://ollama.ai
    pause
    exit /b 1
)

echo.
echo Setup complete! Ollama should now be running.
echo.
pause
