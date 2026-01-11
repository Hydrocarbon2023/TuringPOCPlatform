# 安装和部署指南

本文档面向**首次安装**或**从头开始**的用户。

## 前置要求

### 必需软件

1. **Python 3.8+**
   ```bash
   python3 --version
   ```

2. **Node.js 16+ 和 npm**
   ```bash
   node --version
   npm --version
   ```

3. **MySQL 5.7+ 或 MySQL 8.0+**
   ```bash
   mysql --version
   ```

## 快速开始

### 第一步：克隆项目

```bash
git clone <项目地址>
cd 概念验证平台
```

### 第二步：创建数据库

```bash
# 登录 MySQL
mysql -u root -p

# 创建数据库和用户
CREATE DATABASE poc_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'poc_user'@'localhost' IDENTIFIED BY 'nucifera';
GRANT ALL PRIVILEGES ON poc_platform.* TO 'poc_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 第三步：后端设置

```bash
cd backend

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 初始化数据库（创建所有表）
flask db upgrade

# 如果迁移失败，可以执行 SQL 脚本
mysql -u poc_user -pnucifera poc_platform < create_all_missing_tables.sql

# 启动后端（开发模式）
python app.py
```

后端将在 `http://localhost:5000` 启动

### 第四步：前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动前端（开发模式）
npm start
```

前端将在 `http://localhost:3000` 启动

## 使用自动化脚本（推荐）

### Linux/Mac

```bash
# 1. 确保 MySQL 已安装并运行
# 2. 确保已创建数据库（见上面的第二步）

# 3. 运行安装脚本
chmod +x setup.sh
./setup.sh

# 4. 启动项目
chmod +x start.sh
./start.sh
```

### Windows

```bash
# 1. 确保 MySQL 已安装并运行
# 2. 确保已创建数据库（见上面的第二步）

# 3. 运行安装脚本
setup.bat

# 4. 启动项目
start.bat
```

## 详细步骤

### 1. 数据库配置

编辑 `backend/config.py` 文件，根据你的数据库设置修改连接信息：

```python
class Config:
    SECRET_KEY = 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = 'mysql://用户名:密码@localhost/数据库名'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = 'your-jwt-secret-key-here'
```

### 2. 数据库迁移

项目使用 Flask-Migrate 管理数据库迁移。

```bash
cd backend
source venv/bin/activate  # 激活虚拟环境

# 初始化迁移（仅首次需要）
flask db init  # 如果 migrations 目录不存在

# 创建迁移文件（如果需要）
flask db migrate -m "描述"

# 应用迁移
flask db upgrade
```

### 3. 创建初始数据（可选）

项目目前没有提供初始数据脚本。如果需要，可以：

1. 手动创建管理员账户（通过注册接口或直接插入数据库）
2. 创建测试数据

### 4. 验证安装

1. **检查后端**
   ```bash
   curl http://localhost:5000/api/login
   # 应该返回 405 Method Not Allowed（说明服务正在运行）
   ```

2. **检查前端**
   - 打开浏览器访问 `http://localhost:3000`
   - 应该看到登录页面

## 常见问题

### 1. 数据库连接失败

**错误**：`(2003, "Can't connect to MySQL server")`

**解决**：
- 确保 MySQL 服务正在运行
- 检查 `backend/config.py` 中的数据库连接信息
- 确认数据库用户有权限访问数据库

### 2. 迁移失败

**错误**：`Table 'xxx' doesn't exist`

**解决**：
- 执行 `backend/create_all_missing_tables.sql` 脚本手动创建表
- 或清除 `alembic_version` 表后重新执行迁移

### 3. 端口被占用

**错误**：`Address already in use`

**解决**：
- 后端默认端口：5000，前端默认端口：3000
- 修改端口或关闭占用端口的程序

### 4. 依赖安装失败

**解决**：
- 确保 Python 版本 >= 3.8
- 确保 Node.js 版本 >= 16
- 使用虚拟环境（推荐）
- 检查网络连接（需要下载依赖包）

### 5. CORS 错误

**错误**：`Access-Control-Allow-Origin`

**解决**：
- 确保后端 `CORS` 配置正确
- 检查前端 API 基础 URL 配置

## 生产环境部署

### 后端

1. 使用 Gunicorn 或 uWSGI 作为 WSGI 服务器
2. 使用 Nginx 作为反向代理
3. 配置环境变量存储敏感信息（密钥、数据库密码等）
4. 启用 HTTPS

### 前端

1. 构建生产版本：`npm run build`
2. 使用 Nginx 或 Apache 部署
3. 配置 API 代理

## 下一步

安装完成后：

1. 查看 [README.md](README.md) 了解项目功能
2. 查看 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) 了解架构
3. 查看 [docs/](docs/) 目录下的其他文档

## 获取帮助

如果遇到问题：

1. 查看本文档的"常见问题"部分
2. 查看项目的 Issue 列表
3. 联系项目维护者
