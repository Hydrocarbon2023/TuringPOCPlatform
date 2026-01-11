# 数据库迁移指南

本文档整合了所有数据库迁移相关的说明。

## Flask-Migrate 使用

项目使用 Flask-Migrate 管理数据库迁移，这是推荐的方式。

### 基本命令

```bash
export FLASK_APP=backend/app.py
cd backend

# 初始化迁移（首次运行）
flask db init

# 创建迁移文件
flask db migrate -m "描述性信息"

# 应用迁移
flask db upgrade

# 回退迁移
flask db downgrade

# 查看迁移历史
flask db history

# 查看当前版本
flask db current
```

### 工作流程

1. **修改模型** (`backend/models.py`)
2. **生成迁移文件**: `flask db migrate -m "描述"`
3. **检查迁移文件**: 查看 `backend/migrations/versions/` 下的生成文件
4. **应用迁移**: `flask db upgrade`

### 常见问题

#### 1. 迁移文件冲突

如果多人同时修改了模型，可能出现迁移冲突。解决方法：

```bash
# 先拉取最新迁移
flask db upgrade

# 合并迁移
flask db merge -m "合并迁移"

# 应用合并后的迁移
flask db upgrade
```

#### 2. 手动修改迁移文件

如果自动生成的迁移不正确，可以手动编辑迁移文件。但要确保：
- SQL 语法正确
- 不会破坏现有数据
- 迁移是可逆的

#### 3. 生产环境迁移

在生产环境执行迁移前，**务必**：
1. 备份数据库
2. 在测试环境验证迁移
3. 选择维护窗口执行
4. 准备好回退方案

## 特定功能迁移指南

### 里程碑功能

里程碑表已通过迁移创建。如果遇到问题，请查看：
- 迁移文件：`backend/migrations/versions/e3028893d1b4_create_milestone.py`

### 资源集市功能

资源集市相关表（IncubationResource、ResourceApplication）的迁移请参考：
- [资源集市迁移指南](migration_guide_resource.md)

## 手动 SQL（不推荐）

只有在 Flask-Migrate 无法正常工作时，才考虑手动执行 SQL。

手动执行 SQL 的缺点：
- 无法版本控制
- 难以回退
- 容易出现不一致
- 团队协作困难

如果必须手动执行，请确保：
1. 记录所有执行的 SQL
2. 与团队同步
3. 创建对应的迁移文件记录
