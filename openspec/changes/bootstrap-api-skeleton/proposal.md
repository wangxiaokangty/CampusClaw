## Why

CampusClaw 目前只有一个纯前端演示（React SPA，全部数据 mock，无任何网络请求）。演示已经把产品形态定死了：13 个界面、教师/学生双角色、按班级隔离的数据边界。现在需要把它变成真实的前后端分离应用。

团队约定的开发流程是「先确定接口 → 定好数据格式 → 前后端并行开发」。要让并行真正成立，必须先有一份**可执行的接口契约**——不是文档，而是 FastAPI 自动生成、前端自动消费的 OpenAPI schema。本变更就是建立这份契约，并让全部接口带种子数据跑通，使前端可以立即脱离后端进度独立开发所有页面。

## What Changes

- **新建 FastAPI 后端**（uv 管理环境，SQLModel + SQLite），实现演示中 13 个界面所需的全部接口
- **建立契约管线**：FastAPI OpenAPI → `openapi-typescript` → 前端 `api.d.ts`，前端不手写任何接口类型；CI 校验生成物与提交物一致
- **提取种子数据**：从现有演示 bundle 中还原 2 个班级、6 个学科、讲义与知识块、作业、提交、错题、审计日志，作为 SQLite 初始化数据
- **AI 能力以 mock 实现，但走真实传输通道**：对话走真实 SSE 流式，批改走真实 `BackgroundTasks` 异步；`ai/` 模块是 mock 与真实 LLM 的唯一分界面
- **JWT Bearer 鉴权**，保留演示的「选人登录」体验（`POST /auth/login` 传 `user_id` 直接签发）
- **班级租户隔离**作为依赖注入的横切约束，而非各路由自行过滤
- **Docker 部署**：Next.js standalone + FastAPI，SQLite 挂载 volume
- 非目标：真实 LLM 接入、生产级密码认证、多班级管理后台、真实 MCP 协议握手

## Capabilities

### New Capabilities

- `auth`: 身份认证（JWT 签发与校验）、当前用户上下文、班级租户隔离的强制边界
- `lecture-kb`: 讲义上传与分块入库、讲义列表与删除、班级范围内的知识库关键词检索
- `assistant-config`: 学科助手的提示词编辑、AI 技能增删改与启用开关、技能包（.zip）导入、MCP 服务器连接与工具发现、API Key 保护
- `assistant-chat`: 学生与学科助手的流式对话——技能路由、知识库检索、执行过程（trace）可视化、回答来源引用
- `homework-grading`: 作业发布、学生提交、异步 AI 批改状态机、教师改分覆盖、判错自动生成错题
- `mistake-review`: 学生错题列表与按错因的 AI 讲解
- `care-chat`: 关怀式对话——情绪识别与共情回复，含高风险表达的升级提示
- `learning-analytics`: 学生个人学情画像（知识点雷达、进步曲线、学习风格标签）与教师班级统计
- `skill-audit`: 技能调用审计日志的写入、查询过滤与聚合统计（调用量、失败率、token 用量）

### Modified Capabilities

（无——项目当前没有任何已有 spec。）

## Impact

- **新增** `backend/`：FastAPI 应用（models / schemas / routers / services / ai / seed），`pyproject.toml` + uv 锁定
- **新增** `frontend/`：Next.js 应用骨架与生成的 `types/api.d.ts`
- **新增** `docker-compose.yml` 与两个 Dockerfile
- **数据**：SQLite 单文件，首次启动执行 seed；schema 变更本阶段用重建而非迁移
- **契约风险**：40+ 接口一次性铺开。缓解在于接口形状并非新设计，而是从已存在的演示 state 树反推得出，不确定性主要集中在 `ai/` 模块内部
