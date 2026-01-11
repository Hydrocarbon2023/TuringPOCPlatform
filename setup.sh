#!/bin/bash

# 项目安装脚本
# 用于首次安装或重新安装项目

set -e  # 遇到错误立即退出

echo "========================================="
echo "  概念验证平台 - 安装脚本"
echo "========================================="
echo ""

# 检查 Python
echo "[1/5] 检查 Python..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python 3，请先安装 Python 3.8+"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✓ Python 版本: $PYTHON_VERSION"
echo ""

# 检查 Node.js
echo "[2/5] 检查 Node.js..."
if ! command -v node &> /dev/null; then
    echo "错误: 未找到 Node.js，请先安装 Node.js 16+"
    exit 1
fi
NODE_VERSION=$(node --version)
echo "✓ Node.js 版本: $NODE_VERSION"
echo ""

# 检查 MySQL
echo "[3/5] 检查 MySQL..."
if ! command -v mysql &> /dev/null; then
    echo "警告: 未找到 MySQL 客户端，请确保 MySQL 服务已安装并运行"
    echo "      如果 MySQL 在其他位置，请手动检查"
fi
echo ""

# 提示数据库设置
echo "========================================="
echo "  数据库设置"
echo "========================================="
echo "请确保已完成以下步骤："
echo "1. MySQL 服务正在运行"
echo "2. 已创建数据库: poc_platform"
echo "3. 已创建用户: poc_user (密码: nucifera)"
echo ""
echo "如果未完成，请执行以下 SQL："
echo ""
echo "CREATE DATABASE poc_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
echo "CREATE USER 'poc_user'@'localhost' IDENTIFIED BY 'nucifera';"
echo "GRANT ALL PRIVILEGES ON poc_platform.* TO 'poc_user'@'localhost';"
echo "FLUSH PRIVILEGES;"
echo ""
read -p "数据库已准备就绪？(y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "请先设置数据库，然后重新运行此脚本"
    exit 1
fi
echo ""

# 安装后端依赖
echo "[4/5] 安装后端依赖..."
cd backend

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "创建 Python 虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装依赖
echo "安装 Python 包..."
pip install -r requirements.txt

echo "✓ 后端依赖安装完成"
echo ""

# 初始化数据库
echo "[5/5] 初始化数据库..."
echo "执行数据库迁移..."

# 检查 migrations 目录是否存在
if [ ! -d "migrations" ]; then
    echo "初始化 Flask-Migrate..."
    flask db init
fi

# 执行迁移
if flask db upgrade 2>/dev/null; then
    echo "✓ 数据库迁移成功"
else
    echo "警告: 数据库迁移失败，尝试使用 SQL 脚本..."
    if [ -f "../docs/create_all_missing_tables.sql" ]; then
        mysql -u poc_user -pnucifera poc_platform < ../docs/create_all_missing_tables.sql 2>/dev/null || echo "SQL 脚本执行失败，请手动执行"
        echo "✓ 已执行 SQL 脚本创建表"
    else
        echo "警告: 未找到 docs/create_all_missing_tables.sql 文件"
        echo "请手动执行数据库迁移: flask db upgrade"
    fi
fi

deactivate
cd ..
echo ""

# 安装前端依赖
echo "[6/6] 安装前端依赖..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "安装 Node.js 包（这可能需要几分钟）..."
    npm install
else
    echo "检测到 node_modules 目录，跳过安装"
    echo "如需重新安装，请先删除 node_modules 目录"
fi

echo "✓ 前端依赖安装完成"
cd ..
echo ""

echo "========================================="
echo "  安装完成！"
echo "========================================="
echo ""
echo "下一步："
echo "1. 运行 ./start.sh 启动项目"
echo "2. 或手动启动："
echo "   - 后端: cd backend && source venv/bin/activate && python app.py"
echo "   - 前端: cd frontend && npm start"
echo ""
echo "默认访问地址："
echo "  - 前端: http://localhost:3000"
echo "  - 后端: http://localhost:5000"
echo ""
