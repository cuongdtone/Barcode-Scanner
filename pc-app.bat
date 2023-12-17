@echo off

cd desktop-service

REM Chạy luồng 1
start pythonw server.py

REM Chạy luồng 2
start cmd /k python app.py
