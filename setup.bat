@echo off
python -m venv .venv
call .venv\Scripts\activate

pip install -r backend\requirements.txt
cd frontend && call npm install
cd ..

REM 初始化数据库迁移（如果 migrations 目录不存在）
if not exist "backend\migrations" (
    echo 初始化数据库迁移...
    set FLASK_APP=backend/app.py
    cd backend
    flask db init
    flask db migrate -m "Initial migration"
    cd ..
)

echo "安装成功！下面请运行start.bat启动服务。"
pause
