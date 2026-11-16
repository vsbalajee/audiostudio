@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 scripts\form.py
) else (
  python scripts\form.py
)
if errorlevel 1 (
  echo.
  echo Audio Studio could not start. Install Python 3.10+ with Tkinter and FFmpeg.
  pause
)
