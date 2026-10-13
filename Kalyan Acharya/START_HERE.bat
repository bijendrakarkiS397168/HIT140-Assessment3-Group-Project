@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3.12 -m venv .venv
  if errorlevel 1 (
    echo Python 3.12 is required. Install Python 3.12 and run this file again.
    pause
    exit /b 1
  )
)
".venv\Scripts\python.exe" -m pip install -r requirements-tested.txt
if errorlevel 1 (
  echo Dependency installation failed. Check the message above and your internet connection.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" Kalyan_Acharya_integration.py --out results_reproduced
if errorlevel 1 (
  echo The analysis failed. Keep this window open and share the error.
  pause
  exit /b 1
)
echo Results saved in results_reproduced. The results page should now be open in your browser.
pause
