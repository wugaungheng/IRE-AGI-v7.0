@echo off
cd /d "%~dp0"

:: Launch using the VBS file (which has single-instance check)
wscript.exe launch-v7.vbs
