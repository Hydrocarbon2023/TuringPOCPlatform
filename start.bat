@echo off
if exist ".venv" (call .venv\Scripts\activate) else (call venv\Scripts\activate)

start "Backend Service" cmd /k "python backend/app.py"

cd frontend && npm start
