#!/bin/bash
python3 -m venv .venv
source .venv/bin/activate

pip install -r backend/requirements.txt
cd frontend && npm install

echo "安装成功！下面请运行start.sh启动服务。"
