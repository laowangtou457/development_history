@echo off
setlocal EnableDelayedExpansion
title CodeWatch - Stop Monitor
echo Stopping CodeWatch monitor...
cd /d F:\Develop\code_history
if exist .watch.pid (
    set /p PID=<.watch.pid
    taskkill /PID !PID! /F 2>nul
    timeout /t 1 /nobreak >nul
    if exist .watch.pid del .watch.pid
    echo Stopped PID !PID!
) else (
    echo No running monitor detected.
)
pause
