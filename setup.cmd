@echo off
rem Register Kumiho Desktop's installed 9miho MCP runtime (idempotent).
python "%~dp0scripts\setup.py" %*
