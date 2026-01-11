@echo off
if exist ".venv" (call .venv\Scripts\activate) else (call venv\Scripts\activate)

set FLASK_APP=backend/app.py

echo 正在执行数据库迁移...
cd backend
flask db upgrade
if errorlevel 1 (
    echo 警告: 数据库迁移失败，如果是首次运行，请先执行: flask db init 和 flask db migrate
)
cd ..

start "Backend Service" cmd /k "python backend/app.py"

cd frontend && npm start
