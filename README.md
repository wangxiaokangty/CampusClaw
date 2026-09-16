# CampusClaw

使用 [OpenSpec](https://github.com/Fission-AI/OpenSpec) 的 spec-driven 工作流管理的项目。

## 启动与数据库

前端使用 Next.js，后端使用 FastAPI + SQLModel，运行数据库为 PostgreSQL。

复制 `.env.example` 为 `.env`，填写数据库连接、密码及应用密钥，然后运行：

```sh
docker compose up -d --build
```

访问 `http://localhost:3000`。已有 SQLite 数据需先迁移，再启动新后端。

本地开发、专用测试库、备份迁移及回退步骤见 [PostgreSQL 运行与迁移](docs/postgresql-migration.md)。

前端发布与后端连接步骤见 [Vercel 部署](docs/vercel-deployment.md)。

## 目录结构

```
openspec/
  config.yaml         # OpenSpec 配置（schema: spec-driven）
  specs/              # 主规格
  changes/            # 进行中的变更提案
    archive/          # 已归档的变更
.claude/              # Claude Code 的 skills 与 slash commands
.agents/              # 通用 agent skills
```

## 工作流

| 命令 | 作用 |
| --- | --- |
| `/opsx:explore` | 探索想法、澄清需求 |
| `/opsx:propose` | 创建变更提案及全部产物 |
| `/opsx:apply`   | 按 tasks 实施变更 |
| `/opsx:update`  | 修订已有提案 |
| `/opsx:sync`    | 把 delta spec 同步进主规格 |
| `/opsx:archive` | 完成后归档变更 |
