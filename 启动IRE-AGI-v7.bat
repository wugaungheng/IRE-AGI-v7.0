@echo off
chcp 65001 > nul
echo ================================
echo   IRE-AGI v7.0 启动脚本
echo ================================
echo.

cd /d "C:\Users\Administrator\Desktop\IRE-AGI"

echo [1/3] 正在启动 IRE-AGI v7.0...
echo           PID: %TIME% > "C:\IRE-AGI\last_launch.txt"

"C:\ProgramData\miniconda3\envs\distill\python.exe" ire_agi_v7.py 2> "C:\IRE-AGI\launch_error.txt"

echo.
echo [退出] 程序已退出，错误日志：
type "C:\IRE-AGI\launch_error.txt"
pause
