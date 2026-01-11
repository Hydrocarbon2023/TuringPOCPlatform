# 🚀 图灵数智概念验证平台 (PoC Platform)

基于 Flask + React 的科研项目全生命周期管理系统，支持项目申报、评审、孵化、经费管理等功能。

## 📋 环境要求

- **Python**: 3.8+
- **Node.js**: 16+
- **MySQL**: 8.0+ (需创建数据库 `poc_platform`，字符集 `utf8mb4`)

## ⚙️ 数据库配置

在启动项目前，**必须**先在 MySQL 中执行以下 SQL 语句进行初始化：

```sql
-- 1. 创建数据库 (指定 utf8mb4 以支持 Emoji 表情)
CREATE DATABASE IF NOT EXISTS poc_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. 创建专用用户 (用户名: poc_user, 密码: nucifera)
CREATE USER IF NOT EXISTS 'poc_user'@'localhost' IDENTIFIED BY 'nucifera';

-- 3. 授予权限
GRANT ALL PRIVILEGES ON poc_platform.* TO 'poc_user'@'localhost';

-- 4. 刷新权限
FLUSH PRIVILEGES;
```

> 注意：如需修改数据库配置，请编辑 `backend/config.py` 中的 `SQLALCHEMY_DATABASE_URI`。

## 🛠️ 快速开始

### 第一步：首次安装 (仅需一次)

根据你的系统运行安装脚本，初始化环境并安装依赖。

**Mac/Linux**:
```bash
chmod +x setup.sh start.sh  # 赋予执行权限
./setup.sh
```

**Windows**:
双击运行 `setup.bat`

### 第二步：启动项目

一键启动后端 API 服务和前端 React 界面。

**Mac/Linux**:
```bash
./start.sh
```

**Windows**:
双击运行 `start.bat`

### 第三步：访问应用

浏览器将自动打开 http://localhost:3000

## 📂 项目结构

```
概念验证平台/
├── backend/                  # Flask 后端
│   ├── app.py               # Flask 应用入口
│   ├── config.py            # 配置文件
│   ├── models.py            # 数据库模型
│   ├── exceptions.py        # 自定义异常
│   ├── utils.py             # 工具函数
│   ├── routes.py            # 路由注册
│   ├── resources/           # API 资源模块
│   │   ├── auth.py          # 认证相关
│   │   ├── users.py         # 用户管理
│   │   ├── teams.py         # 团队管理
│   │   ├── projects.py      # 项目管理
│   │   └── ...              # 其他功能模块
│   ├── migrations/          # 数据库迁移文件
│   └── requirements.txt     # Python 依赖
├── frontend/                # React 前端
│   ├── src/
│   │   ├── api/             # API 客户端
│   │   ├── components/      # 通用组件
│   │   ├── pages/           # 页面组件
│   │   └── styles/          # 样式主题
│   └── package.json         # Node 依赖
├── docs/                    # 文档目录
│   ├── migration_guide.md   # 数据库迁移指南
│   └── visualization_guide.md # 数据可视化指南
└── README.md                # 项目说明（本文件）
```

## 🎯 核心功能

### 1. 项目管理
- 项目申报与提交
- 项目状态跟踪（待初审、初审中、复审中、公示中、已通过等）
- 项目领域分类
- 成熟度等级管理（研发阶段、小试阶段、中试阶段、小批量生产阶段）

### 2. 团队管理
- 团队创建与管理
- 团队成员邀请
- 团队角色分配（队长/成员）

### 3. 评审系统
- 评审任务分配
- 多维度评分（创新性、可行性、团队协作、产业化潜力）
- 评审意见提交
- 评审进度跟踪

### 4. 孵化管理
- 产业孵化计划制定
- 概念验证（PoC）管理
- 里程碑跟踪
- 孵化进度管理

### 5. 经费管理
- 经费下拨记录
- 支出报销管理
- 经费余额查询
- 经费使用统计

### 6. 成果管理
- 成果录入
- 成果展示
- 成果与项目关联

### 7. 企业对接
- 企业支持者注册
- 对接意向管理
- 资源集市（企业发布资源，项目申请对接）

### 8. 数据可视化
- 项目统计图表
- 经费使用分析
- 评审数据可视化
- 孵化进度展示

## 👥 用户角色

- **项目参与者**: 申报项目、管理项目、提交报销等
- **评审人**: 评审项目、提交评审意见、查看孵化项目
- **秘书**: 项目审核、任务分配、系统管理
- **管理员**: 用户管理、系统配置、数据查看
- **企业支持者**: 发布资源、对接项目、查看孵化项目

## 🔐 默认账号

首次运行时请先注册账号。支持注册的角色包括：
- 项目参与者
- 评审人
- 秘书
- 企业支持者

管理员账号需由现有管理员创建。

## 📝 数据库迁移

项目使用 Flask-Migrate 管理数据库迁移。

### 首次迁移

如果 `migrations` 目录不存在，需要初始化：

```bash
export FLASK_APP=backend/app.py
cd backend
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 后续迁移

每次运行 `start.sh` 或 `start.bat` 时会自动执行 `flask db upgrade`。

如需手动迁移：

```bash
export FLASK_APP=backend/app.py
cd backend
flask db migrate -m "描述性信息"
flask db upgrade
```

### 故障排查

如果遇到数据库相关错误，请检查：
1. MySQL 服务是否正常运行
2. 数据库用户权限是否足够
3. 数据库字符集是否为 `utf8mb4`
4. 迁移文件是否正确生成

## 🛡️ 开发指南

### 后端开发

1. **添加新的 API 端点**:
   - 在 `backend/resources/` 目录下创建或修改相应的资源文件
   - 在 `backend/routes.py` 中注册路由

2. **数据库模型变更**:
   - 修改 `backend/models.py`
   - 运行 `flask db migrate -m "描述"`
   - 运行 `flask db upgrade`

3. **代码规范**:
   - 使用 Python 3.8+ 语法
   - 遵循 PEP 8 代码风格
   - 添加适当的注释和文档字符串

### 前端开发

1. **添加新页面**:
   - 在 `frontend/src/pages/` 下创建页面组件
   - 在 `frontend/src/App.js` 中添加路由

2. **添加新组件**:
   - 在 `frontend/src/components/` 下创建通用组件
   - 使用 Ant Design 组件库

3. **API 调用**:
   - 在 `frontend/src/api/api.js` 中添加 API 客户端方法
   - 使用统一的错误处理

## 📚 相关文档

### 用户指南
- [快速开始指南](QUICK_START.md) ⭐ - **新用户必读**，5分钟快速安装
- [安装和部署指南](INSTALLATION.md) - 详细的安装说明和常见问题

### 开发文档
- [项目架构文档](docs/ARCHITECTURE.md) - 详细的架构说明和模块划分
- [数据库迁移指南](docs/migration_guide.md) - 数据库迁移操作指南
- [数据可视化指南](docs/visualization_guide.md) - 数据可视化功能使用指南

完整文档目录请查看 [docs/README.md](docs/README.md)
