# PostgreSQL 运行与迁移

本项目运行数据库为 PostgreSQL，应用继续使用同步 SQLModel 会话。页面、认证、接口、流式对话和批改流程保持原样。SQLite 仅作为一次性迁移的源数据格式。

日期继续使用原有无时区语义；提交带时区的作业截止时间时，保存钟面时间并去掉时区，不进行时区换算，与原 SQLite 行为一致。

## 新安装：Docker Compose

在项目根目录复制配置：

```sh
cp .env.example .env
```

编辑 `.env`，设置 `POSTGRES_USER`、`POSTGRES_PASSWORD`、`POSTGRES_DB`、`CAMPUSCLAW_DATABASE_URL` 和 `CAMPUSCLAW_JWT_SECRET`。Compose 内的连接地址使用主机名 `db`，例如：

```text
postgresql+psycopg://campusclaw:密码的URL编码@db:5432/campusclaw
```

密码中的 `@`、`/`、`#` 等字符需要在连接地址中百分号编码；`POSTGRES_PASSWORD` 使用原始密码。密码包含 `$` 时，`.env` 中使用单引号包裹值，避免 Compose 插值。示例密码仅为占位，不应直接用于部署。已有安装保持原认证密钥和其他非数据库设置。

```sh
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

访问 `http://localhost:3000`。数据库健康后后端才启动；空库自动建表并装载演示数据，重启不重复装载。前端继续通过同源 `/api` 访问后端，后端 `/health` 成功响应仍为 `{"status":"ok"}`。

PostgreSQL 数据保存在 `campusclaw-postgres` 命名卷（实际名称带 Compose 项目前缀）。普通容器重建保留数据；不要使用 `docker compose down -v` 删除数据卷。原 SQLite 卷不会被迁移工具删除，也不能把旧 SQLite 卷当 PostgreSQL 卷挂载。

镜像使用 PostgreSQL 17，初始化指定 UTF-8 编码和 `C` 排序规则，维持中文和字符串排序。连接已有外部 PostgreSQL 时，应使用相同编码与排序规则创建空库；初始化参数只对新建的数据目录生效。连接地址也支持 `postgresql://`，会规范化为 Psycopg 3 驱动；外部服务所需 `sslmode` 等连接参数可保留在地址中。

## 宿主机开发

先按上节配置根目录 `.env`，只启动数据库并开放本机端口：

```sh
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db
cd backend
uv sync --frozen
```

为后端创建自己的 `backend/.env`，连接主机使用 `127.0.0.1` 而不是 `db`，默认端口为 5432；如端口冲突，在根目录 `.env` 设置 `POSTGRES_PORT`，同时更新后端地址。

```text
CAMPUSCLAW_DATABASE_URL=postgresql+psycopg://campusclaw:密码的URL编码@127.0.0.1:5432/campusclaw
```

```sh
uv run uvicorn app.main:app --reload
```

缺失或错误的数据库配置会使启动失败，不会回退到 SQLite。旧的 `CAMPUSCLAW_DATABASE_PATH` 不再是运行配置。前端开发命令不变。

## 测试

使用独立的测试数据库。以下命令在项目根目录运行（若修改了用户名，相应替换 `campusclaw`）：

```sh
docker compose exec db createdb -U campusclaw -T template0 --encoding=UTF8 --locale=C campusclaw_test
```

在 `backend/.env.test` 中设置专用连接地址：

```text
CAMPUSCLAW_TEST_DATABASE_URL=postgresql+psycopg://campusclaw:密码的URL编码@127.0.0.1:5432/campusclaw_test
```

```sh
cd backend
uv run --env-file .env.test pytest -q
cd ../frontend
npm run check:api
```

测试账号需有测试库内创建及删除 schema（模式）的权限。每个测试只清理自己随机命名的 schema，请求、启动逻辑和后台任务共享该 schema。未设置测试地址时直接报错；不要把测试地址指向业务数据库。OpenAPI 导出与类型校验不连接数据库。

## 存量 SQLite 迁移

### 1. 停写并备份

保留旧版本代码/镜像、旧配置与 SQLite 数据卷，停止旧后端及后台任务。不要先启动新后端，否则自动种子会使目标不再为空。

使用 SQLite 备份接口制作一致快照。下面在项目根目录执行，备份路径可按环境修改；输出文件必须不存在：

```sh
python3 - <<'PY'
import sqlite3
from pathlib import Path

source = Path('backend/data/campusclaw.db').resolve()
backup = Path('backups/campusclaw-before-postgresql.db').resolve()
if not source.is_file() or backup.exists():
    raise SystemExit('源文件不存在，或备份文件已存在；请检查路径')
backup.parent.mkdir(parents=True, exist_ok=True)
with sqlite3.connect(source.as_uri() + '?mode=ro', uri=True) as src:
    with sqlite3.connect(backup) as dst:
        src.backup(dst)
        assert dst.execute('PRAGMA integrity_check').fetchone() == ('ok',)
print('备份及完整性检查完成')
PY
```

不要仅复制正在使用的主 `.db` 文件；WAL（Write-Ahead Logging，预写日志）中的已提交记录也必须进入快照。备份含完整业务数据，应与数据库凭据一样妥善保管。

### 2. 只启动空 PostgreSQL，执行迁移

配置新的根目录 `.env`，其中连接地址指向 Compose 内的 `db`。在项目根目录执行：

```sh
docker compose up -d db
docker compose build backend
docker compose run --rm --no-deps -v ./backups:/backup:ro backend python scripts/migrate_sqlite_to_postgresql.py /backup/campusclaw-before-postgresql.db
```

也可以用宿主机执行；在 `backend/.env` 中设置目标 PostgreSQL 地址后运行：

```sh
cd backend
uv run python scripts/migrate_sqlite_to_postgresql.py ../backups/campusclaw-before-postgresql.db
```

工具不启动 Web 应用、不装载种子。它只读源文件，检查全部业务表和字段、外键、枚举及布尔值，在一个目标事务内按外键依赖写入并校验记录数量、主键和全部字段。成功输出 `verified: true` 与各表数量，退出码为 0；失败退出码为 1，事务回滚。JSON（JavaScript Object Notation，JavaScript 对象表示法）的对象键顺序不影响内容比较，数组顺序和 SQL NULL/JSON null 的区别均保留。

任一目标业务表非空就拒绝迁移，包括已装载的演示数据或之前成功迁入的数据。不要为重试而清空有业务记录的目标库；应选择新的空数据库。失败后可对仍为空的目标重试。工具不自动修复、删除或跳过不兼容数据。

### 3. 切换与验收

确认迁移成功，再启动完整服务：

```sh
docker compose up -d --build
```

开放用户写入前，核对教师/学生登录、讲义与助手、历史对话、流式回答、作业批改、错题、审计、关怀隐私及学情。验证跨班访问仍为 404，旧数据没有被种子覆盖。已有滞留批改会按原规则在启动时恢复，应记录这部分预期写入。

在测试环境创建记录后运行 `docker compose up -d --force-recreate`，确认记录仍在。实际切换保持原有认证密钥、代理、域名和其他非数据库配置；本变更不自动修改线上服务。

### 4. 回退

在开放用户写入前验收失败：停止新后端，恢复旧版本/镜像、旧配置及一致 SQLite 备份，使用原 `CAMPUSCLAW_DATABASE_PATH` 启动旧版本。保留新 PostgreSQL 数据用于诊断。新版本不支持切回 SQLite，必须同时恢复旧代码。

开放写入后不能直接用旧 SQLite 快照回退，否则会丢失新记录。此时停止写入，优先修复 PostgreSQL 或从其备份恢复；本工具不提供自动反向迁移。
