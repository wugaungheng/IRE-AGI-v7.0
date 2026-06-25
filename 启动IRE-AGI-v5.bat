@echo off
chcp 65001 > nul
set HF_ENDPOINT=https://hf-mirror.com
set PYTHON=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe
set SCRIPT_DIR=C:\Users\Administrator\Desktop\IRE-AGI

cd /d "%SCRIPT_DIR%"

echo ==============================
echo   IRE-AGI v5.0 智能版
echo   聊天 + 数据分析 + 自我演化
echo ==============================
echo.

"%PYTHON%" ire_agi_v5.py
if errorlevel 1 (
    echo.
    echo [X] 启动失败，请查看上方错误信息
    pause
)
