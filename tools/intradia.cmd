@echo off
rem Vigilancia intradía de QQQ cada 5 minutos (D48). Solo paper trading: no envía órdenes reales.
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
"C:\Users\matia\AppData\Local\Programs\Python\Python312\python.exe" -m copilot intradia >> logs\intradia.log 2>&1
exit /b 0
