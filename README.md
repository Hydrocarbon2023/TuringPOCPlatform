# 🚀 图灵数智概念验证平台 (PoC Platform)

基于 Flask + React 的科研项目全生命周期管理系统。

## 📋 环境要求
- **Python**: 3.8+
- **Node.js**: 16+
- **MySQL**: 8.0+ (需创建数据库 `poc_platform`，字符集 `utf8mb4`)

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
