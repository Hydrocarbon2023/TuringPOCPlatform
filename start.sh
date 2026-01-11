#!/bin/bash

trap 'kill $(jobs -p); exit' SIGINT

# 激活虚拟环境
source .venv/bin/activate || source venv/bin/activate

# 设置 Flask 应用环境变量
export FLASK_APP=backend/app.py

# 运行数据库迁移
echo "正在执行数据库迁移..."
cd backend && flask db upgrade
if [ $? -ne 0 ]; then
    echo "警告: 数据库迁移失败，如果是首次运行，请先执行: flask db init 和 flask db migrate"
fi
cd ..

# 启动后端服务
python backend/app.py &

# 启动前端服务
cd frontend && npm start
