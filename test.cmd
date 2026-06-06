@echo off
setlocal
set "PYTHON=C:\Users\nguye\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%PYTHON%" (
  where python >nul 2>nul
  if errorlevel 1 (
    echo [ERROR] Python 3.11+ was not found.
    echo Install it from https://www.python.org/downloads/windows/
    exit /b 1
  )
  set "PYTHON=python"
)
"%PYTHON%" -m unittest discover -s "%~dp0tests" -v
exit /b %errorlevel%
