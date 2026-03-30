@echo off
set "SCRIPT=%~dp0export_markdown_pdf.ps1"

where pwsh >nul 2>nul
if %errorlevel%==0 (
    pwsh -NoLogo -NoProfile -File "%SCRIPT%" %*
) else (
    powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%" %*
)
