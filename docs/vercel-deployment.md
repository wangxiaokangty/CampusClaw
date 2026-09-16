# Vercel 部署

前端项目为 `xiaokang2/campusclaw`，访问地址为 <https://campusclaw-eight.vercel.app>。
部署目录为 `frontend/`，框架选择 Next.js。

后端项目为 `xiaokang2/campusclaw-api`，访问地址为 <https://campusclaw-api.vercel.app>，健康检查为 `/health`。
数据库为 Vercel Marketplace 中的 Neon 免费资源 `campusclaw-db`，仅连接后端的 Production 环境。

## 发布前端

在仓库根目录执行（需要已安装并登录 Vercel CLI（Command Line Interface，命令行工具））：

```sh
cd frontend
npm ci
npm run build
vercel link --project campusclaw
vercel --prod
```

`.vercel/` 和本地环境变量文件不提交到仓库。

## 部署 FastAPI 后端和数据库

前后端均使用 Vercel：`campusclaw` 部署 `frontend/`，`campusclaw-api` 部署 `backend/`。
PostgreSQL 通过 Vercel Marketplace 的 Neon 集成创建，数据库实际由 Neon 托管。
无需使用 Render。

`backend/server.py` 是 Vercel 入口，复用现有 FastAPI 应用；当未显式设置 `CAMPUSCLAW_DATABASE_URL` 时，读取 Neon 自动注入的 `DATABASE_URL`。
后端与数据库均选择 `iad1` 区域。`backend/vercel.json` 将单次函数执行时限配置为 300 秒。

```sh
cd backend
vercel link --project campusclaw-api
vercel integration add neon --name campusclaw-db --plan free_v3 \
  --metadata region=iad1 --metadata auth=false \
  --environment production --no-env-pull
vercel env add CAMPUSCLAW_JWT_SECRET production --sensitive
vercel --prod
```

首次安装 Neon 时，Vercel 要求账号本人通过命令返回的浏览器链接接受集成条款，再重试安装命令。
`CAMPUSCLAW_JWT_SECRET` 必须使用独立随机生成的密钥。数据库连接信息不提交到仓库，也不填入前端的 `NEXT_PUBLIC_*` 变量。
具体数据库说明见 [PostgreSQL 运行与迁移](postgresql-migration.md)。

## 连接前端

前端项目的 Production 环境已设置 `API_PROXY_TARGET=https://campusclaw-api.vercel.app`。值为后端 HTTPS 根地址，不含末尾斜杠和 `/api`。浏览器请求同源 `/api/*`，Next.js 将其转发给后端。

```sh
cd frontend
vercel env add API_PROXY_TARGET production
vercel --prod
```

`API_PROXY_TARGET` 在构建时生效，因此修改后必须重新部署。使用同源代理时无需设置 `NEXT_PUBLIC_API_BASE`。

## 验证

- `/login` 应返回 HTTP（Hypertext Transfer Protocol，超文本传输协议）200。
- 连接后端后，`/api/users` 应返回账号列表，且能选择身份进入页面。
- 未连接后端时，仅能访问前端页面，登录、对话和作业等功能不可用。
- 当前登录方式为无需密码的演示登录，适用于演示数据。

## 本次验证记录（2026-09-17）

前端依赖已更新至 Next.js 15.5.25、React 19.1.9，本地生产构建及类型检查通过。
`npm audit --omit=dev` 仍报告 3 项依赖问题（1 项中危、2 项高危），涉及 PostCSS 和 sharp 及其对 Next.js 的影响；本次未进行 Next.js 跨主版本升级。

Neon 免费数据库已创建并连接后端，随机生成的登录签名密钥已配置为 Vercel Secret。FastAPI 后端部署完成，`/health` 返回 200，数据库初始化完成，教师与学生登录及身份查询通过。

本地 PostgreSQL、登录、作业和对话测试共 67 项通过；Vercel 入口的 `DATABASE_URL` 适配及显式应用配置优先级验证通过。

前端重新发布并接通后端后，通过正式域名完成以下线上验证：

- `/login` 返回 200，`/api/users` 返回 4 个演示账号。
- 教师、学生登录及当前身份查询成功。
- 对话流依次包含 `trace`、`delta`、`done` 事件，回答保存到数据库。
- 发布和提交测试作业成功，轮询观察到 `submitted → grading → graded`，评分及依据均已保存。
- 跨班级读取提交返回 404，作业列表保持班级隔离。

线上保留一份明确标记的“部署联调验证（测试作业）”（`hw-5c186548a65a`）及相应提交和测试对话，便于复查。
本轮未完成浏览器交互验证，因为当前浏览器连接不可用；上述结果来自正式域名上的实际接口请求。

当前通过本地 CLI 发布。GitHub 自动部署尚未连接：Vercel 提示账号需先添加 GitHub Login Connection；这不影响当前部署及手动更新。

参考：[Vercel FastAPI](https://vercel.com/docs/frameworks/backend/fastapi)、[Vercel PostgreSQL](https://vercel.com/docs/postgres)。
