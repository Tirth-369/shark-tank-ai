@echo off
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (
  echo [ERROR] Virtual environment not found.
  echo Create it with: py -3.11 -m venv venv
  pause
  exit /b 1
)
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe train_models.py
pause
