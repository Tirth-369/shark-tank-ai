@echo off
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (
  echo [ERROR] Virtual environment not found.
  echo First run: py -3.11 -m venv venv
  echo Then run: venv\Scripts\python.exe -m pip install -r requirements_tkinter.txt
  pause
  exit /b 1
)
venv\Scripts\python.exe tkinter_app.py
pause
