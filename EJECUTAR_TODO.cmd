@echo off
cd /d "%~dp0"
python reproducir.py
if errorlevel 1 echo La ejecucion no termino correctamente. Revise el mensaje anterior.
pause
