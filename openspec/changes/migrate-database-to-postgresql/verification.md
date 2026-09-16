# PostgreSQL 迁移验证记录

验证日期：2026-09-17。验证在本机临时 PostgreSQL 17 和隔离 Compose 项目中完成，未访问或切换线上服务。

## 自动化结果

- 修改前：原有 215 项 SQLite 后端测试全部通过。
- 修改后：237 项 PostgreSQL 测试全部通过，保留原业务断言；新增数据库、迁移及兼容性用例。仍有原依赖的两条弃用提示，无测试失败。
- SQLite 接口基线保存在 `backend/tests/fixtures/sqlite_contract.json`，覆盖教师/学生账号、身份、讲义、助手、作业、看板、学情、错题、审计及模拟评分结果。PostgreSQL 输出与基线一致。
- 全部 14 张表的历史记录迁移、微秒日期、嵌套 JSON、布尔值、枚举、SQL NULL 与 JSON null 均有测试覆盖。
- 目标非空、重复执行、源字段缺失、未知表、非法枚举、非法布尔值、孤立外键、连接失败、写入失败及内容校验失败均拒绝迁移；失败不留下部分业务记录。
- 带时区截止时间经对照发现存在存储差异，已通过 `WallClockDateTime` 保留原 SQLite 的钟面时间语义；回归测试通过。

执行命令：

```sh
cd backend
uv sync --frozen
uv run --env-file /private/tmp/campusclaw-pg-test.env pytest -q
cd ../frontend
npm run check:api
```

## 契约与容器

- 前后 OpenAPI 文件逐字节一致，SHA-256 为 `682f269470c88dad21ff58b5307ec57c23e68c31831c009ae7b491b0f5286dc7`；`npm run check:api` 通过，前端源代码与生成类型未修改。
- Compose 配置校验、前后端镜像构建、PostgreSQL 就绪后后端启动及前端启动均通过。
- 通过 `http://localhost:3000/api` 验证登录、作业创建、带时区截止时间输入、异步批改，以及 SSE（Server-Sent Events，服务器发送事件）的 trace/delta/done 事件。
- 创建作业、批改结果和对话后，用 `docker compose up -d --force-recreate` 重建数据库、后端、前端容器，验证同一数据卷中记录完整保留，提交与对话内容逐字段一致。
- 浏览器页面交互验收待完成：当前 Chrome/内置浏览器连接均不可用，已询问连接或临时浏览器方案；任务 5.3 暂不勾选。

## 存量迁移与回退演练

1. 通过 SQLite 备份接口从本地现有数据库生成只读迁移快照，`PRAGMA integrity_check` 通过，源库保持原样。
2. 向独立的 `campusclaw_rehearsal` 空 PostgreSQL 数据库执行迁移脚本，14 张表均报告校验成功。
3. 使用迁入库启动新版本，确认不重复 seed；读取账号、讲义、助手、作业、教师看板和审计。
4. 从 Git 当前提交提取旧版本代码到临时目录，用原配置方式和快照恢复 SQLite，旧版本成功启动并登录。
5. 新版本 PostgreSQL 与恢复的旧版本 SQLite 对上述接口返回值逐字节比较一致。

新安装与存量操作步骤见 `docs/postgresql-migration.md`。开放写入后的自动反向迁移不在本变更范围内。
