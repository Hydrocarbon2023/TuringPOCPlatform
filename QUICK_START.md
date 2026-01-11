# 快速开始指南

> 适用于**完全没有数据库**的新用户

## 5 分钟快速安装

### 1️⃣ 安装 MySQL（如果还没有）

**macOS**:
```bash
brew install mysql
brew services start mysql
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql
```

**Windows**:
下载并安装 MySQL：https://dev.mysql.com/downloads/mysql/

### 2️⃣ 创建数据库（2 分钟）

```bash
# 登录 MySQL（需要 root 权限）
mysql -u root -p

# 执行以下 SQL（或直接执行 INIT_DATABASE.sql 文件）
CREATE DATABASE IF NOT EXISTS poc_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'poc_user'@'localhost' IDENTIFIED BY 'nucifera';
GRANT ALL PRIVILEGES ON poc_platform.* TO 'poc_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

或者直接执行脚本：
```bash
mysql -u root -p < INIT_DATABASE.sql
```

### 3️⃣ 运行安装脚本（2 分钟）

```bash
# Linux/Mac
chmod +x setup.sh
./setup.sh

# Windows
setup.bat
```

安装脚本会自动：
- ✅ 检查 Python 和 Node.js
- ✅ 创建虚拟环境
- ✅ 安装所有依赖
- ✅ 初始化数据库表结构

### 4️⃣ 启动项目（1 分钟）

```bash
# Linux/Mac
./start.sh

# Windows
start.bat
```

### 5️⃣ 访问应用

浏览器会自动打开 http://localhost:3000

## 手动安装（如果脚本不工作）

### 后端

```bash
cd backend

# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库
flask db upgrade
# 如果迁移失败，执行：
mysql -u poc_user -pnucifera poc_platform < create_all_missing_tables.sql

# 4. 启动后端
python app.py
```

### 前端

```bash
cd frontend

# 1. 安装依赖
npm install

# 2. 启动前端
npm start
```

## 常见问题

### Q: 数据库连接失败？

A: 检查：
1. MySQL 服务是否运行：`mysql -u root -p` 能否登录
2. 数据库和用户是否创建：执行 `INIT_DATABASE.sql`
3. 配置文件：`backend/config.py` 中的连接信息

### Q: 迁移失败？

A: 
1. 尝试执行 `backend/create_all_missing_tables.sql` 手动创建表
2. 或查看 `FIX_MIGRATION.md` 了解详细解决方案

### Q: 端口被占用？

A: 
- 后端端口：5000（可在 `app.py` 修改）
- 前端端口：3000（可在 `package.json` 修改）

### Q: Python 模块找不到？

A: 
1. 确保已激活虚拟环境：`source venv/bin/activate`
2. 重新安装依赖：`pip install -r requirements.txt`

## 下一步

安装成功后：

1. 📖 查看 [README.md](README.md) 了解项目功能
2. 📚 查看 [INSTALLATION.md](INSTALLATION.md) 了解详细配置
3. 🏗️ 查看 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) 了解架构

## 需要帮助？

- 查看 [INSTALLATION.md](INSTALLATION.md) 的"常见问题"部分
- 查看项目的 Issue 列表
- 联系项目维护者
