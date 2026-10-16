@echo off
setlocal
cd /d "%~dp0"
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
  "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" "%~dp0ABRIR_VISOR.py"
) else (
  py -3 "%~dp0ABRIR_VISOR.py"
)
if errorlevel 1 pause
endlocal
