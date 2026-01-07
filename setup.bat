@echo off
python -m venv .venv
call .venv\Scripts\activate

pip install -r backend\requirements.txt
cd frontend && call npm install

echo "安装成功！下面请运行start.bat启动服务。"
pause
