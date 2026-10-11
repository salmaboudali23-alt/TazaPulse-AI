@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Installez les dependances en suivant README.md avant de lancer.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m streamlit run app.py
pause
