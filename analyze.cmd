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
if "%~1"=="" (
  echo Usage: analyze.cmd PROJECT_PATH [--provider none^|openai^|ollama]
  exit /b 1
)
"%PYTHON%" "%~dp0main.py" analyze %*
exit /b %errorlevel%
