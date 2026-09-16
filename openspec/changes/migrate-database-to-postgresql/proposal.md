## Why

按项目要求，将 CampusClaw 的持久化数据库由 SQLite 切换为 PostgreSQL，同时保持现有用户体验、业务行为和接口契约。现有连接初始化、容器存储和测试夹具绑定 SQLite，需要一起调整，避免仅修改连接地址导致部署失败或行为偏差。

## What Changes

- 将应用运行和集成测试的数据库切换为 PostgreSQL，保留 SQLModel 与同步会话模式。
- **BREAKING（部署配置）**：用 `CAMPUSCLAW_DATABASE_URL` 替代 `CAMPUSCLAW_DATABASE_PATH`；不再以 SQLite 文件作为运行数据库。此变化仅限运维配置。
- 为 Docker Compose 增加 PostgreSQL 服务、就绪检查和持久化卷，保持现有前后端服务、对外端口和代理路径。
- 提供 SQLite 存量数据的一次性迁移、完整性校验及切换回退说明，保留记录标识、关联和业务值。
- 用真实 PostgreSQL 验证初始化、种子数据、后台批改与全部现有接口测试；确认 OpenAPI 契约及前端生成类型无变化。

## Capabilities

### New Capabilities

- `postgresql-persistence`：定义 PostgreSQL 连接、初始化和持久化运行、存量数据迁移以及既有行为兼容的验收要求。

### Modified Capabilities

无。主规格目录目前没有已登记能力；`bootstrap-api-skeleton` 中已有业务增量规格保持原样，本变更不重新定义业务需求。

## Impact

- 后端：`app/config.py`、`app/db.py`、驱动依赖及 `uv.lock`；必要的存储类型、排序兼容调整限于维持既有行为。
- 部署与开发：`backend/Dockerfile`、`docker-compose.yml`、`backend/tests/conftest.py`，新增迁移脚本及相关测试、Markdown 操作说明。
- 文档：更新 README 和实施时的 `openspec/config.yaml` 技术栈描述；原启动方案中的 SQLite 设计作为历史保留，由本变更取代其数据库部署决策。
- 前端页面、API（Application Programming Interface，应用程序编程接口）路径与响应、认证、班级隔离、人工智能模拟能力、流式事件、异步批改状态和种子数据内容均保持不变。
- 不引入异步数据库架构、缓存、任务队列、业务表重设计或通用数据库版本迁移框架；本提案不执行生产切换。
