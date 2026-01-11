# 发布检查清单

## ✅ 项目整理状态

### 文档整理
- ✅ 删除了临时/重构相关文档（REFACTORING_*.md, PROJECT_REFACTORING.md等）
- ✅ 保留核心用户文档（README.md, QUICK_START.md, INSTALLATION.md）
- ✅ 文档统一放在 `docs/` 目录
- ✅ 创建了 `docs/README.md` 作为文档索引

### SQL 脚本整理
- ✅ 保留 `INIT_DATABASE.sql`（根目录，用于首次创建数据库）
- ✅ 删除了临时SQL脚本（create_all_missing_tables.sql, create_resource_tables.sql等）
- ✅ 数据库表结构通过 Flask-Migrate 管理

### 代码整理
- ✅ 已完成模块拆分（resources/目录）
- ✅ 修复了命名冲突（IncubationResource -> IncubationResourceAPI）
- ✅ 代码结构清晰，便于维护

## 📋 发布前检查

### 环境要求
- [ ] Python 3.8+ 已安装
- [ ] Node.js 16+ 已安装
- [ ] MySQL 5.7+ 或 8.0+ 已安装并运行

### 数据库
- [ ] 数据库初始化脚本（INIT_DATABASE.sql）测试通过
- [ ] 数据库迁移（flask db upgrade）测试通过
- [ ] 所有表结构正确创建

### 功能测试
- [ ] 用户注册/登录功能正常
- [ ] 项目管理功能正常
- [ ] 团队管理功能正常
- [ ] 评审功能正常
- [ ] 孵化管理功能正常
- [ ] 资源集市功能正常
- [ ] 数据可视化功能正常

### 文档
- [x] README.md 信息完整
- [x] QUICK_START.md 可以指导新用户安装
- [x] INSTALLATION.md 包含详细说明
- [x] docs/ 目录文档完整（已整理，只保留必要文档）

### 配置文件
- [ ] backend/config.py 配置正确
- [ ] 敏感信息（密钥、密码）已提醒用户修改
- [ ] .gitignore 已配置（不提交敏感信息）

### 依赖
- [ ] backend/requirements.txt 完整
- [ ] frontend/package.json 完整
- [ ] 所有依赖可以正常安装

## 🚀 发布步骤

1. **代码审查**
   - 检查代码质量和规范
   - 确保没有调试代码
   - 确保错误处理完善

2. **测试**
   - 完整功能测试
   - 性能测试（如需要）
   - 安全性检查

3. **文档更新**
   - 更新版本号（如需要）
   - 检查所有文档链接
   - 确认安装说明准确

4. **打包准备**
   - 确保 .gitignore 正确配置
   - 准备发布说明（CHANGELOG）
   - 创建发布标签（如使用 Git）

5. **发布**
   - 提交代码
   - 创建发布版本
   - 更新文档链接

## 📝 注意事项

- **数据库配置**：提醒用户修改默认密码和密钥
- **环境变量**：生产环境应使用环境变量存储敏感信息
- **日志**：生产环境应配置适当的日志级别
- **安全**：确保所有安全最佳实践已实施

## 🔗 相关文档

- [README.md](README.md) - 项目概览
- [QUICK_START.md](QUICK_START.md) - 快速开始
- [INSTALLATION.md](INSTALLATION.md) - 安装指南
- [docs/](docs/) - 详细文档
