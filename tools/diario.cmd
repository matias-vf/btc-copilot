@echo off
rem Ciclo diario del copiloto (paper trading). Solo análisis: no envía órdenes reales.
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
echo ===== %date% %time% >> logs\diario.log
"C:\Users\matia\AppData\Local\Programs\Python\Python312\python.exe" -m copilot hoy >> logs\diario.log 2>&1
"C:\Users\matia\AppData\Local\Programs\Python\Python312\python.exe" -m copilot hoy oro >> logs\diario.log 2>&1
"C:\Users\matia\AppData\Local\Programs\Python\Python312\python.exe" -m copilot verificar >> logs\diario.log 2>&1
git add registros >> logs\diario.log 2>&1
git diff --cached --quiet || git commit -q -m "paper: ciclo diario %date%" >> logs\diario.log 2>&1
exit /b 0
