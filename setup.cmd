@echo off
rem Register Kumiho Desktop's installed 9miho MCP runtime (idempotent).
set "MIHO_EXE=%USERPROFILE%\.kumiho\apps\9miho\bin\9miho.exe"
if not exist "%MIHO_EXE%" (
  echo 9miho is not installed. Install or repair it in Kumiho Desktop. 1>&2
  exit /b 2
)
"%MIHO_EXE%" --setup-agent-hosts %*
exit /b %ERRORLEVEL%
