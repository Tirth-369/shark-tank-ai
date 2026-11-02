@echo off
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (
  echo [ERROR] Virtual environment not found.
  echo First run: py -3.11 -m venv venv
  pause
  exit /b 1
)
venv\Scripts\python.exe -m pip install -r requirements_tkinter.txt
if not exist data.csv (
  if exist "data(2).csv" copy /Y "data(2).csv" data.csv >nul
)
venv\Scripts\python.exe "train_models(1).py"
pause
