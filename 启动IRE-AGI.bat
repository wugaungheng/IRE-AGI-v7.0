@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ===============================
echo   IRE-AGI v4.0 自我演化引擎
echo   武光衡理论 · 桌面版
echo ===============================
echo.

set PYTHON=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe

REM 检查依赖
"%PYTHON%" -c "import torch, sklearn; print('[OK] 依赖已就绪')" 2>nul
if errorlevel 1 (
    echo [!] 正在安装依赖，请稍候...
    "%PYTHON%" -m pip install torch scikit-learn numpy --quiet
)

echo [*] 正在启动 IRE-AGI...
"%PYTHON%" ire_agi.py --gui
if errorlevel 1 (
    echo.
    echo [X] 启动失败，请查看上方错误信息
    pause
)
