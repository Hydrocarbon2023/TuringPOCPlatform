# 🚀 图灵数智概念验证平台 (PoC Platform)

基于 Flask + React 的科研项目全生命周期管理系统。

## 📋 环境要求
- **Python**: 3.8+
- **Node.js**: 16+
- **MySQL**: 8.0+ (需创建数据库 `poc_platform`，字符集 `utf8mb4`)

## ⚙️ 数据库配置 (关键步骤)

项目默认配置使用特定的数据库账号和密码。在启动项目前，**必须**先在 MySQL 中执行以下 SQL 语句进行初始化：

打开终端或 MySQL 客户端：
    ```bash
    mysql -u root -p
    ```
执行以下 SQL 语句：

    ```SQL
    -- 1. 创建数据库 (指定 utf8mb4 以支持 Emoji 表情)
    CREATE DATABASE IF NOT EXISTS poc_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    
    -- 2. 创建专用用户 (用户名: poc_user, 密码: nucifera)
    -- 注意：如果您的 MySQL 版本较老(5.x)，语法可能略有不同
    CREATE USER IF NOT EXISTS 'poc_user'@'localhost' IDENTIFIED BY 'nucifera';
    
    -- 3. 授予权限
    GRANT ALL PRIVILEGES ON poc_platform.* TO 'poc_user'@'localhost';
    
    -- 4. 刷新权限
    FLUSH PRIVILEGES;
    ```
注意：配置文件的路径为 backend/config.py。如果您想修改密码或数据库名，请记得同步修改该文件中的 SQLALCHEMY_DATABASE_URI。

## 🛠️ 快速开始

### 第一步：首次安装 (仅需一次)
根据你的系统运行安装脚本，初始化环境并安装依赖。

- **Mac/Linux**: 
  ```bash
  chmod +x setup.sh start.sh  # 赋予执行权限
  ./setup.sh

- **Windows**:
  双击运行 setup.bat

### 第二步：启动项目
一键启动后端 API 服务和前端 React 界面。

Mac/Linux: ./start.sh

Windows: 双击运行 start.bat

### 第三步：访问
浏览器将自动打开 http://localhost:3000

## 📂 目录结构
/backend: Flask 后端代码 (API, 数据库模型)

/frontend: React 前端代码 (界面, 交互)

requirements.txt: 后端依赖清单

start.* / setup.*: 自动化脚本

## 🔑 默认账号 (测试用)
首次运行时请先注册一个管理员账号。
