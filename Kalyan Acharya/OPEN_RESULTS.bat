@echo off
cd /d "%~dp0"
if exist "results_reproduced\RESULTS.html" (
  start "" "results_reproduced\RESULTS.html"
) else (
  start "" "results\RESULTS.html"
)
