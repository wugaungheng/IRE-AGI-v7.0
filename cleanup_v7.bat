@echo off
title IRE-AGI Cleanup Tool
color 0A

echo ============================================================
echo   IRE-AGI v7.0 - Safe Cleanup Tool
echo ============================================================
echo.
echo This script will:
echo   1. Move old versions to OldVersions folder (backup)
echo   2. Keep only v7.0 files
echo.
echo Press any key to continue...
pause > nul

cd /d "%~dp0"

REM Create backup folder
if not exist "OldVersions" mkdir OldVersions

echo.
echo [1/3] Backing up old versions...
echo ------------------------------------------------------------

REM Move old Python files
if exist "ire_agi_v5.py" (
    move "ire_agi_v5.py" "OldVersions\" > nul
    echo   ✅ Moved ire_agi_v5.py to OldVersions/
)

if exist "ire_agi_v5_1.py" (
    move "ire_agi_v5_1.py" "OldVersions\" > nul
    echo   ✅ Moved ire_agi_v5_1.py to OldVersions/
)

if exist "ire_agi_v5_2.py" (
    move "ire_agi_v5_2.py" "OldVersions\" > nul
    echo   ✅ Moved ire_agi_v5_2.py to OldVersions/
)

if exist "ire_agi_v6.py" (
    move "ire_agi_v6.py" "OldVersions\" > nul
    echo   ✅ Moved ire_agi_v6.py to OldVersions/
)

REM Move old batch files
if exist "启动IRE-AGI-v5.bat" (
    move "启动IRE-AGI-v5.bat" "OldVersions\" > nul
    echo   ✅ Moved 启动IRE-AGI-v5.bat to OldVersions/
)

if exist "启动IRE-AGI-v5.1.bat" (
    move "启动IRE-AGI-v5.1.bat" "OldVersions\" > nul
    echo   ✅ Moved 启动IRE-AGI-v5.1.bat to OldVersions/
)

if exist "启动IRE-AGI-v5.2.bat" (
    move "启动IRE-AGI-v5.2.bat" "OldVersions\" > nul
    echo   ✅ Moved 启动IRE-AGI-v5.2.bat to OldVersions/
)

if exist "启动IRE-AGI-v5.vbs" (
    move "启动IRE-AGI-v5.vbs" "OldVersions\" > nul
    echo   ✅ Moved 启动IRE-AGI-v5.vbs to OldVersions/
)

if exist "启动IRE-AGI-v5.1.vbs" (
    move "启动IRE-AGI-v5.1.vbs" "OldVersions\" > nul
    echo   ✅ Moved 启动IRE-AGI-v5.1.vbs to OldVersions/
)

if exist "启动IRE-AGI-v6.bat" (
    move "启动IRE-AGI-v6.bat" "OldVersions\" > nul
    echo   ✅ Moved 启动IRE-AGI-v6.bat to OldVersions/
)

echo.
echo [2/3] Cleaning up auxiliary files...
echo ------------------------------------------------------------

REM Move old VBS scripts (keep only v7 related)
if exist "cleanup-and-shortcut.vbs" (
    move "cleanup-and-shortcut.vbs" "OldVersions\" > nul
    echo   ✅ Moved cleanup-and-shortcut.vbs to OldVersions/
)

if exist "create_desktop_shortcut.vbs" (
    move "create_desktop_shortcut.vbs" "OldVersions\" > nul
    echo   ✅ Moved create_desktop_shortcut.vbs to OldVersions/
)

if exist "create_shortcut.vbs" (
    move "create_shortcut.vbs" "OldVersions\" > nul
    echo   ✅ Moved create_shortcut.vbs to OldVersions/
)

if exist "diagnose.py" (
    move "diagnose.py" "OldVersions\" > nul
    echo   ✅ Moved diagnose.py to OldVersions/
)

if exist "diagnose.vbs" (
    move "diagnose.vbs" "OldVersions\" > nul
    echo   ✅ Moved diagnose.vbs to OldVersions/
)

if exist "diagnose_launch.vbs" (
    move "diagnose_launch.vbs" "OldVersions\" > nul
    echo   ✅ Moved diagnose_launch.vbs to OldVersions/
)

if exist "fix_and_start.vbs" (
    move "fix_and_start.vbs" "OldVersions\" > nul
    echo   ✅ Moved fix_and_start.vbs to OldVersions/
)

if exist "launch-hidden.vbs" (
    move "launch-hidden.vbs" "OldVersions\" > nul
    echo   ✅ Moved launch-hidden.vbs to OldVersions/
)

if exist "launch.vbs" (
    move "launch.vbs" "OldVersions\" > nul
    echo   ✅ Moved launch.vbs to OldVersions/
)

if exist "make_desktop_shortcut_v2.vbs" (
    move "make_desktop_shortcut_v2.vbs" "OldVersions\" > nul
    echo   ✅ Moved make_desktop_shortcut_v2.vbs to OldVersions/
)

if exist "make_shortcut.py" (
    move "make_shortcut.py" "OldVersions\" > nul
    echo   ✅ Moved make_shortcut.py to OldVersions/
)

if exist "put-on-desktop.vbs" (
    move "put-on-desktop.vbs" "OldVersions\" > nul
    echo   ✅ Moved put-on-desktop.vbs to OldVersions/
)

if exist "run_experiment_v7.bat" (
    move "run_experiment_v7.bat" "OldVersions\" > nul
    echo   ✅ Moved run_experiment_v7.bat to OldVersions/
)

if exist "start_v7.bat" (
    move "start_v7.bat" "OldVersions\" > nul
    echo   ✅ Moved start_v7.bat to OldVersions/
)

if exist "创建快捷方式.vbs" (
    move "创建快捷方式.vbs" "OldVersions\" > nul
    echo   ✅ Moved 创建快捷方式.vbs to OldVersions/
)

echo.
echo [3/3] Cleanup complete!
echo ------------------------------------------------------------
echo.
echo ✅ All old versions moved to: OldVersions/
echo ✅ Kept v7.0 files:
dir /b "ire_agi_v7.py" 2> nul
echo.
echo ⚠️  To permanently delete old versions:
echo    1. Check OldVersions/ folder
echo    2. If everything works, delete OldVersions/ folder
echo.
echo Press any key to exit...
pause > nul
