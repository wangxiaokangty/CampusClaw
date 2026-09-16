## Context

参见 proposal.md「Why」。

约束来自两个方向。**产品形态已冻结**：现有前端演示（React SPA）已经定义了 13 个界面和完整的数据形状，本变更的接口不是新设计，而是从演示的 state 树反推得出——这大幅降低了一次性铺开 40+ 接口的设计风险。**团队流程要求并行**：前后端必须能在契约确定后各自推进，因此契约必须是机器可验证的，而不是一份会腐烂的 Markdown。

技术栈已定：Next.js / FastAPI（uv）/ SQLModel / SQLite / Docker。

## Goals / Non-Goals

**Goals:**

- 契约漂移在 CI 阶段就失败，而不是在联调阶段才发现
- 前端在后端业务逻辑完成前即可开发全部 13 个界面
- mock AI 与真实 LLM 的替换面积收敛到单个模块，替换时路由、契约、前端零改动
- 班级隔离是结构性保证，不依赖每个路由作者记得加过滤条件

**Non-Goals:**

- 数据库迁移工具链（本阶段 schema 变更靠重建 + reseed）
- 水平扩展与并发写入优化（SQLite 单写者足够覆盖演示与课程答辩场景）
- 真实 MCP 协议实现（连接与工具发现为模拟行为，见 `assistant-config` spec）

## Decisions

### D1：后端 OpenAPI 为契约的唯一真相，前端生成类型

FastAPI 从 Pydantic schema 自动导出 `openapi.json`，前端用 `openapi-typescript` 生成 `types/api.d.ts`，前端不手写任何接口类型定义。CI 中重新生成并 `git diff --exit-code`，不一致即失败。

*备选方案*：(a) 手写 OpenAPI yaml 作为真相，前后端都从它生成——更"契约优先"，但多一份需要人工同步的产物，且 FastAPI 的实现容易与之偏离而不被发现；(b) 前端手写 TS 接口类型——零工具成本，但漂移必然发生且只能靠联调发现。选择当前方案是因为它让"后端实现"和"契约"物理上不可能不一致。

*代价*：契约的可读形态依赖后端代码。因此 Pydantic schema 的字段命名与 docstring 需要按「给前端看」的标准来写。

### D2：`models/`（SQLModel table）与 `schemas/`（Pydantic）严格分离

SQLModel 允许用 `table=True` 的模型直接作为 `response_model`，本项目禁止这样做。每个实体至少有 `XxxRead` / `XxxCreate` / `XxxUpdate` 三类 schema。

*理由*：`Assistant` 表含 `api_key`，直接返回即泄漏。现有演示前端专门实现了打码函数 `wv()`，说明这是已知的敏感字段。更一般地，表结构服务于存储，接口形状服务于消费者，二者的演化速度不同——耦合它们会让任何一次存储重构都变成破坏性的契约变更。

*代价*：样板代码增加。接受，因为它换来的是 D1 的契约稳定性。

### D3：班级租户隔离通过依赖注入强制，而非路由自觉

提供 `get_current_user` 与 `get_class_scope` 依赖；所有涉及班级数据的查询必须经由 scope 对象构造，而不是直接使用裸 session。

*备选方案*：每个路由自行 `where(class_id == user.class_id)`——演示前端就是这么做的（每个 selector 都手写 filter）。在只读的 mock 里可行，在有写入和 40+ 接口的真实后端里，漏掉一处就是跨班数据泄漏，而且这类缺陷不会在正常测试中暴露。

*验证方式*：针对每个班级作用域端点，用 B 班用户请求 A 班资源，断言 404（而非 403——不泄漏资源存在性）。

### D4：`ai/` 是 mock 与真实 LLM 的唯一分界面

对外签名固定，mock 与真实实现二选一注入：

```
answer(assistant, question, chunks) -> AsyncIterator[Event]   # trace / delta / done
grade(homework, submission, chunks) -> GradeResult
explain_mistake(mistake, chunks)    -> str
profile(student_stats)              -> LearnerProfile
detect_emotion(text)                -> CareReply
```

关键约束：**mock 实现必须走真实的传输通道**。对话真的经 SSE 逐段推送，批改真的经 `BackgroundTasks` 异步执行并真的经历 `submitted → grading → graded` 状态迁移。

*理由*：如果 mock 走同步返回，那么前端针对流式渲染、轮询、加载态、竞态取消所写的代码在换真模型时全部作废——等于把集成风险推迟到最后。让传输层从第一天就是真的，mock 的只是内容生成。

### D5：对话用 SSE，不用 WebSocket

`POST /conversations/{id}/messages` 返回 `text/event-stream`，事件类型 `trace` / `delta` / `done`。

*理由*：对话是单向流（一次请求、一个流式响应），SSE 恰好匹配且在 FastAPI（`StreamingResponse`）和浏览器端都无需额外依赖。WebSocket 需要连接生命周期管理、重连、心跳，收益为零。

*已知代价*：SSE 走 POST 时不能用原生 `EventSource`，前端需用 `fetch` + `ReadableStream` 手动解析。可接受。

### D6：异步批改用 BackgroundTasks + 客户端轮询

提交返回 201 与 `state=submitted`，后台任务推进状态，前端轮询 `GET /submissions/{id}` 直到 `graded`。

*备选方案*：Celery + Redis——正确的生产方案，但为单文件 SQLite 应用引入两个额外服务，Docker 拓扑复杂度翻倍，与本阶段目标不成比例。

*已知代价*：进程重启会丢失进行中的任务。缓解：启动时扫描 `state=grading` 且超过阈值的记录，重新入队。

### D7：JWT Bearer + 选人登录

`POST /auth/login` 接受 `user_id` 直接签发 JWT，保留演示中「点头像切换身份」的体验。密码校验位于同一端点内，是后续唯一需要改动的地方。

*理由*：演示的核心价值之一就是快速切换教师/学生/A班/B班来展示隔离效果，加密码会破坏这个演示动线。同时后端侧已是标准 Bearer 鉴权，不存在"演示专用的假鉴权"这种需要重写的中间态。

*安全边界*：此登录方式明确不适用于生产。记录在 spec 中作为显式约束，而非隐含假设。

### D8：学情分析是计算结果，不是存储

`learning-analytics` 的所有端点实时计算，不建表。

演示中部分指标是**哈希伪随机**（`uf(studentId, subject)`、写死的 `activity = [12,18,9,24,30,21,34]`、`of(name) % 3` 决定学习风格）。本变更照搬这些确定性函数，理由是它们保证雷达图与曲线在演示中数值稳定且视觉合理。同时，凡是真实数据已足够计算的指标——正确率、提交数、错题数、技能调用次数——一律接真值。

每个伪随机指标在代码中标注 `TODO(real-metric)`，构成一份明确的待偿清单，而不是散落的魔法数字。

### D9：嵌套结构的存储选择

`Skill` 与 `McpServer` 独立建表（它们有完整的增删改查接口与独立生命周期）；`sources` / `trace` / `keywords` / `bound_lecture_ids` 使用 `Column(JSON)`（它们总是随宿主整体读写，无独立查询需求）。

*判据*：是否存在针对该结构的独立端点或查询条件。有则建表，无则 JSON 列。

### D10：Docker 拓扑

两个镜像、一个 compose。Next.js 用 standalone 输出以缩小镜像；SQLite 文件挂 named volume 以便容器重建后数据留存；后端容器启动时若数据库为空则执行 seed。

开发态前端直连后端（`NEXT_PUBLIC_API_BASE`），生产态由 Next.js rewrites 反代 `/api` 到后端服务名，避免浏览器侧跨域配置。

## Risks / Trade-offs

- **40+ 接口一次性铺开，其中部分可能从未被前端调用** → 接口形状源自已存在的演示 state 树，而非凭空设计；每个端点在 spec 中绑定到具体界面，无界面归属的端点不实现
- **SQLite 写并发有限（单写者）** → 演示与答辩场景的并发量远低于阈值；仅需确保 `BackgroundTasks` 中的批改写入不与请求写入长事务重叠
- **mock AI 的输出质量可能误导对真实效果的预期** → 界面保留演示中已有的「演示数据」标注；`ai/` 模块的 mock 实现独立命名（`ai/mock.py`），不伪装成真实实现
- **种子数据从压缩后的 JS bundle 提取，可能有遗漏或转写错误** → 提取过程脚本化而非手抄，并以「前端渲染结果与原演示逐屏对照」作为验收方式
- **无迁移工具，schema 变更靠重建** → 本阶段数据全部可从 seed 重建，无用户产生的持久数据；一旦出现真实数据即需引入 Alembic，这是本设计的明确失效边界
- **关怀式对话涉及学生心理状态** → 不做心理诊断，不存储情绪标签用于评价；高风险关键词触发固定的求助引导文案，该行为写入 spec 而非留给实现自由发挥

## Migration Plan

全新项目，无存量数据与向后兼容负担。

1. 后端骨架 + 数据模型 + seed，`/docs` 可见完整接口列表
2. 生成 `api.d.ts` 并提交，契约冻结 → **前后端在此点分叉并行**
3. 后端按能力逐个填实现；前端按界面逐个对接
4. Docker compose 打通

回滚策略：契约冻结前的任何变更直接改；冻结后的破坏性契约变更需同步更新 `api.d.ts` 并在 PR 中显式标注 **BREAKING**。

## Open Questions

- 讲义分块策略（按页 / 按固定长度 / 按标题层级）在真实文档上的效果未知。本阶段种子数据已是切好的块，上传路径用简单的按段落切分即可跑通；真实效果调优待接入真实文档后再定，不影响接口形状。
- 是否需要对话历史的分页。当前演示中单个会话消息量很小，先返回全量；若真实使用中出现长会话，加 cursor 分页是纯增量变更。
