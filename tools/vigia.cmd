@echo off
rem Vigía horario del copiloto (D33): solo observa el mercado. No genera señales ni órdenes.
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
"C:\Users\matia\AppData\Local\Programs\Python\Python312\python.exe" -m copilot vigia >> logs\vigia.log 2>&1
exit /b 0
