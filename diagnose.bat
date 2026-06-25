@echo off
title IRE-AGI v7.0 Diagnose
cd /d "%~dp0"

echo ============================================================
echo   IRE-AGI v7.0 - Diagnostic Tool
echo   Checking each component step by step
echo ============================================================
echo.

python diagnose.py 2>&1

echo.
pause
