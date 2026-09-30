@echo off
setlocal EnableDelayedExpansion
title CodeWatch - Code Change Monitor
echo ========================================
echo   CodeWatch Code Change Monitor
echo   Log dir: F:\Develop\code_history
echo ========================================
echo.
cd /d F:\Develop\code_history

rem Check if already running (verify PID is really alive, avoid stale lock)
if exist .watch.pid (
    set /p OLD_PID=<.watch.pid
    tasklist /FI "PID eq !OLD_PID!" | findstr /I "!OLD_PID!" >nul
    if not errorlevel 1 (
        echo Already running PID !OLD_PID! - run stop_watch.bat to restart.
        pause
        exit /b
    )
    echo Stale PID !OLD_PID! not alive - cleaning up and continuing.
    del .watch.pid
)

echo Starting monitor (pythonw in background)...
start "" pythonw.exe watch_changes.py
timeout /t 2 /nobreak >nul
if exist .watch.pid (
    set /p NEW_PID=<.watch.pid
    echo Monitor started, PID: !NEW_PID!
) else (
    echo Start FAILED - check that pythonw is available.
)
echo.
pause
