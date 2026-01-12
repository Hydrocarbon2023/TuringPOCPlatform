# 项目架构文档

## 📁 项目结构

```
概念验证平台/
├── backend/                      # Flask 后端
│   ├── app.py                   # Flask 应用初始化（~70行）
│   ├── app_new.py               # 新的简化版本（参考）
│   ├── config.py                # 配置文件
│   ├── models.py                # 数据库模型（SQLAlchemy）
│   ├── exceptions.py            # 自定义异常类
│   ├── utils.py                 # 工具函数
│   ├── routes.py                # 路由注册（~140行）
│   ├── resources/               # API 资源模块
│   │   ├── __init__.py
│   │   ├── auth.py              # 认证模块（Login, Register）
│   │   ├── users.py             # 用户管理（AdminUserResource）
│   │   ├── teams.py             # 团队管理
│   │   ├── projects.py          # 项目管理
│   │   ├── secretary.py         # 秘书功能
│   │   ├── reviewer.py          # 评审功能
│   │   ├── incubation.py        # 孵化管理
│   │   ├── funds.py             # 经费管理
│   │   ├── achievements.py      # 成果管理
│   │   ├── milestones.py        # 里程碑管理
│   │   ├── comments.py          # 评论管理
│   │   ├── supporter.py         # 企业支持者
│   │   ├── marketplace.py       # 资源集市
│   │   └── statistics.py        # 统计数据
│   └── migrations/              # 数据库迁移文件
│
├── frontend/                    # React 前端
│   ├── src/
│   │   ├── api/                 # API 客户端
│   │   ├── components/          # 通用组件
│   │   ├── pages/               # 页面组件
│   │   └── styles/              # 样式主题
│   └── package.json
│
└── docs/                        # 文档目录
    ├── ARCHITECTURE.md          # 架构文档（本文件）
    ├── migration_guide.md       # 数据库迁移指南
    └── visualization_guide.md   # 数据可视化指南
```

## 🏗️ 架构设计

### 后端架构

#### 1. 应用初始化（app.py）

**职责**：
- Flask 应用创建和配置
- 扩展初始化（数据库、JWT、CORS、Migrate）
- 全局错误处理
- 路由注册

**代码量**：约70行

#### 2. 数据库模型（models.py）

**职责**：
- 定义所有数据库表结构
- SQLAlchemy 模型类
- 数据验证方法

#### 3. 异常处理（exceptions.py）

**职责**：
- 定义自定义异常类
- APIException（基类）
- ValidationError（验证错误）
- NotFoundError（资源未找到）
- PermissionError（权限错误）

#### 4. 工具函数（utils.py）

**职责**：
- get_current_user() - 获取当前登录用户
- create_default_milestones() - 创建默认里程碑

#### 5. 路由注册（routes.py）

**职责**：
- 导入所有 Resource 类
- 统一注册所有 API 路由
- 管理路由映射

#### 6. 资源模块（resources/）

**注：resources目前尚未投入使用，现在的代码仍在app.py基础上运行。**

**职责**：
- 实现具体的业务逻辑
- 每个模块负责一个功能领域
- 使用 Flask-RESTful 的 Resource 类

**模块列表**：

1. **auth.py** - 认证模块
   - Login（登录）
   - Register（注册）

2. **users.py** - 用户管理
   - AdminUserResource（管理员用户管理）

3. **teams.py** - 团队管理
   - TeamResource（团队列表/创建）
   - MyTeamsResource（我的团队）
   - TeamMembersResource（团队成员管理）

4. **projects.py** - 项目管理
   - ProjectResource（项目列表/详情/创建）

5. **secretary.py** - 秘书功能
   - ProjectAudit（项目初审）
   - TaskAssignment（评审任务分配）

6. **reviewer.py** - 评审功能
   - ReviewerTasksResource（评审任务列表）
   - ReviewerIncubationProjectsResource（评审人孵化项目）
   - ReviewerReview（提交评审意见）
   - NotificationResource（通知管理）

7. **incubation.py** - 孵化管理
   - IncubationResource（孵化计划管理）
   - ProofOfConceptResource（概念验证列表/创建）
   - ProofOfConceptDetailResource（概念验证详情/更新）

8. **funds.py** - 经费管理
   - FundResource（经费下拨）
   - ExpenditureResource（支出报销）
   - ProjectFundsResource（项目经费详情）

9. **achievements.py** - 成果管理
   - AchievementResource（上传成果）
   - ProjectAchievementsResource（项目成果列表）

10. **milestones.py** - 里程碑管理
    - ProjectMilestonesResource（项目里程碑列表）
    - MilestoneUpdateResource（更新里程碑状态）

11. **comments.py** - 评论管理
    - ProjectCommentsResource（项目留言列表/发表）

12. **supporter.py** - 企业支持者
    - SupporterProjectsResource（浏览孵化项目）
    - SupportIntentionResource（提交对接意向）
    - ProjectIntentionsResource（项目收到的对接意向）

13. **marketplace.py** - 资源集市
    - SupporterResourcesResource（发布/查看资源）
    - ResourceApplicationsResource（查看资源申请）
    - ApplicationHandleResource（处理申请）
    - PublicResourcesResource（浏览开放资源）
    - ResourceApplyResource（申请资源）
    - MyResourceApplicationsResource（我的申请进度）

14. **statistics.py** - 统计数据
    - StatisticsResource（全局统计）
    - UserStatisticsResource（用户个人统计）
    - ReviewerStatisticsResource（评审人统计）
    - SupporterStatisticsResource（企业支持者统计）

### 前端架构

#### 1. API 客户端（api/api.js）

**职责**：
- 封装所有 API 调用
- 统一错误处理
- Token 管理

#### 2. 通用组件（components/）

**职责**：
- 可复用的 UI 组件
- GlassCard（毛玻璃卡片）
- ChartCard（图表卡片）
- StatCard（统计卡片）
- AnimatedButton（动画按钮）

#### 3. 页面组件（pages/）

**职责**：
- 不同角色的仪表板
- 登录/注册页面
- 项目管理页面

## 🔄 数据流

### 请求处理流程

```
客户端请求
  ↓
Flask 路由（routes.py）
  ↓
Resource 类（resources/*.py）
  ↓
业务逻辑处理
  ↓
数据库操作（models.py）
  ↓
返回响应
```

### 权限控制流程

```
请求到达
  ↓
@jwt_required() 装饰器
  ↓
get_current_user() 获取用户
  ↓
检查用户角色和权限
  ↓
执行或拒绝操作
```

## 🎯 设计原则

1. **单一职责**：每个模块只负责一个功能领域
2. **模块化**：代码按功能拆分到不同文件
3. **可维护性**：清晰的代码结构和注释
4. **可扩展性**：新增功能只需添加新的资源模块
5. **一致性**：统一的错误处理和代码风格

## 📊 代码统计

- **原 app.py**: 2355行
- **新 app.py**: ~70行（减少 97%）
- **resources 模块**: 15个文件，约2542行
- **routes.py**: ~140行
- **总计**: 约2752行（包括注释和空行）

## 🔧 开发指南

### 添加新功能

1. 在 `resources/` 目录下创建新的模块文件
2. 实现 Resource 类
3. 在 `routes.py` 中导入并注册路由
4. 测试功能

### 修改现有功能

1. 找到对应的资源模块文件
2. 修改相应的 Resource 类
3. 测试修改后的功能

### 调试

- 查看日志输出（日志级别：INFO）
- 检查异常处理（exceptions.py）
- 使用 Flask 调试模式
