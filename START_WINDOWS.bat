@echo off
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 (
 echo Please install Python 3.
 pause
 exit /b 1
)
py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
start http://127.0.0.1:8000
python -m uvicorn app:app --host 127.0.0.1 --port 8000
pause
