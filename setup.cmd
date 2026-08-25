@echo off
rem Register miho-mcp with the agent hosts on this machine (idempotent).
python "%~dp0scripts\setup.py" %*
