@echo off

REM
start .\output\server\server.exe

netsh advfirewall firewall add rule name="Allow Server App" dir=in action=allow program=".\output\server\server.exe" enable=yes

REM
start .\output\app\app.exe
