@echo off
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (
  echo [ERROR] Virtual environment not found.
  echo Create it with: py -3.11 -m venv venv
  pause
  exit /b 1
)
venv\Scripts\python.exe -m streamlit run streamlit_app.py
pause
