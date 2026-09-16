/**
 * 由 `npm run gen:api` 从后端 OpenAPI 自动生成 —— 请勿手工编辑。
 */

export interface paths {
    "/api/analytics/class": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 班级统计
         * @description 教师专属。技能调用次数与学生人数为真实值；活跃度序列为演示数据。
         */
        get: operations["class_stats_api_analytics_class_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/analytics/student/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 我的学情分析
         * @description 提交数、正确率、错题数为真实值；掌握度基准、趋势历史段与学习风格为确定性演示数据（相同输入恒产生相同输出）。
         */
        get: operations["my_analytics_api_analytics_student_me_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/assistants": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 助手列表 */
        get: operations["list_assistants_api_assistants_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/assistants/{assistant_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 助手详情 */
        get: operations["get_assistant_api_assistants__assistant_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /**
         * 修改提示词与绑定讲义
         * @description 教师专属。绑定的讲义必须与助手同班同学科。
         */
        patch: operations["update_assistant_api_assistants__assistant_id__patch"];
        trace?: never;
    };
    "/api/assistants/{assistant_id}/mcp-servers": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** MCP 服务器列表 */
        get: operations["list_mcp_servers_api_assistants__assistant_id__mcp_servers_get"];
        put?: never;
        /**
         * 连接 MCP 服务器
         * @description 教师专属。**本阶段握手为模拟行为**，不发起真实 MCP 协议通信，返回的工具列表由服务器地址推导而来。
         */
        post: operations["add_mcp_server_api_assistants__assistant_id__mcp_servers_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/assistants/{assistant_id}/mcp-servers/{server_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /**
         * 断开 MCP 服务器
         * @description 教师专属。内置服务器不可删除；删除后相关技能的工具绑定被同步清理。
         */
        delete: operations["delete_mcp_server_api_assistants__assistant_id__mcp_servers__server_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/assistants/{assistant_id}/skills": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 技能列表 */
        get: operations["list_skills_api_assistants__assistant_id__skills_get"];
        put?: never;
        /** 新增自定义技能 */
        post: operations["create_skill_api_assistants__assistant_id__skills_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/assistants/{assistant_id}/skills/{skill_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** 删除自定义技能 */
        delete: operations["delete_skill_api_assistants__assistant_id__skills__skill_id__delete"];
        options?: never;
        head?: never;
        /**
         * 修改技能 / 启停
         * @description 教师专属。内置必需技能可停用但不可删除。
         */
        patch: operations["update_skill_api_assistants__assistant_id__skills__skill_id__patch"];
        trace?: never;
    };
    "/api/assistants/{assistant_id}/skills/import": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * 解析技能包（.zip）
         * @description 教师专属。解析包内 skill.json 并返回供确认；缺少清单时返回可识别内容并标注需人工补全，不自动创建技能。
         */
        post: operations["import_skill_api_assistants__assistant_id__skills_import_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/audit/logs": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 审计日志
         * @description 教师专属。按时间降序分页，可按技能、结果状态、用户过滤。
         */
        get: operations["list_logs_api_audit_logs_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/audit/stats": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 审计统计
         * @description 教师专属。总调用次数、失败率、总 token 用量与按技能的分项。
         */
        get: operations["read_stats_api_audit_stats_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/auth/login": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * 选人登录
         * @description 凭账号标识签发 JWT。**演示用途，不校验密码，不适用于生产环境。**
         */
        post: operations["login_api_auth_login_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/auth/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 当前用户
         * @description 返回当前令牌对应的用户、所属班级与该班已开设的学科。
         */
        get: operations["read_me_api_auth_me_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/care/messages": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 我的关怀对话
         * @description 仅本人可读。
         */
        get: operations["my_care_messages_api_care_messages_get"];
        put?: never;
        /**
         * 发送关怀对话消息
         * @description 返回识别到的情绪与共情回应。检测到高风险表达时 `escalated` 为 true，回应中附加固定的求助引导文案。**不做心理诊断。**
         */
        post: operations["send_care_message_api_care_messages_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/conversations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * 获取或创建会话
         * @description 同一「用户 + 助手」组合幂等：已存在则返回既有会话及其历史消息。
         */
        post: operations["ensure_conversation_api_conversations_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/conversations/{conversation_id}/messages": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 会话历史
         * @description 按时间升序返回。助手消息保留当时的技能标识、来源引用与执行过程。
         */
        get: operations["list_messages_api_conversations__conversation_id__messages_get"];
        put?: never;
        /**
         * 发送消息（SSE 流式）
         * @description 以 text/event-stream 响应，事件依次为：
         *     - `trace` —— 执行过程步骤 `{icon, label, detail}`
         *     - `delta` —— 回答文本增量 `{text}`
         *     - `done` —— 结束 `{message_id, skill_key, sources, tokens, cost_ms}`
         *     - `error` —— 生成失败 `{detail}`，流就此终止
         *
         *     每个事件的 `data` 载荷形状见 `ChatStreamEvent`；客户端中途断开不会留下半条损坏的消息。
         */
        post: operations["send_message_api_conversations__conversation_id__messages_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/dashboard/student": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 学生首页看板 */
        get: operations["student_dashboard_api_dashboard_student_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/dashboard/teacher": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 教师首页看板 */
        get: operations["teacher_dashboard_api_dashboard_teacher_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/homeworks": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 作业列表
         * @description 学生视角附带本人提交状态，且不含他人提交内容；教师视角附带提交份数。
         */
        get: operations["list_homeworks_api_homeworks_get"];
        put?: never;
        /** 发布作业 */
        post: operations["create_homework_api_homeworks_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/homeworks/{homework_id}/submissions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 某作业的全部提交
         * @description 教师专属。
         */
        get: operations["list_submissions_api_homeworks__homework_id__submissions_get"];
        put?: never;
        /**
         * 提交作业
         * @description 立即返回，不等待批改。重复提交会覆盖旧提交并重新批改，此前的 AI 评分被清除。轮询 `GET /submissions/{id}` 获取批改进展。
         */
        post: operations["submit_api_homeworks__homework_id__submissions_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/kb/search": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 知识库检索
         * @description 在本班知识库中按关键词检索，结果标注讲义标题与位置。无命中返回空列表。
         */
        get: operations["search_kb_api_kb_search_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/lectures": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 讲义列表 */
        get: operations["list_lectures_api_lectures_get"];
        put?: never;
        /**
         * 上传讲义
         * @description 教师专属。文件被切分为知识块入库，每块记录位置标识与关键词。
         */
        post: operations["upload_lecture_api_lectures_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/lectures/{lecture_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /**
         * 删除讲义
         * @description 教师专属。同时删除其知识块，并从所有助手的绑定列表中移除该讲义。
         */
        delete: operations["delete_lecture_api_lectures__lecture_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/lectures/{lecture_id}/chunks": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 讲义的知识块 */
        get: operations["list_chunks_api_lectures__lecture_id__chunks_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/mistakes/{mistake_id}/explain": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * 错题讲解
         * @description 基于错因与本班知识库生成讲解并附来源。讲解持久化后重复请求直接返回既有内容，不重复生成、不重复计 token。
         */
        post: operations["explain_api_mistakes__mistake_id__explain_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/mistakes/mine": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 我的错题
         * @description 仅返回当前学生自己的错题。
         */
        get: operations["my_mistakes_api_mistakes_mine_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/submissions/{submission_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 提交详情（轮询批改状态） */
        get: operations["get_submission_api_submissions__submission_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/submissions/{submission_id}/review": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /**
         * 教师改分
         * @description 教师专属。仅对已批改的提交可用。AI 原始评分保留，不被抹除。
         */
        patch: operations["review_api_submissions__submission_id__review_patch"];
        trace?: never;
    };
    "/api/submissions/mine": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 我的提交 */
        get: operations["my_submissions_api_submissions_mine_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/users": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 可选账号列表
         * @description 登录界面用。无需认证，且不返回任何凭据字段。
         */
        get: operations["list_users_api_users_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 健康检查 */
        get: operations["health_health_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** AssistantRead */
        AssistantRead: {
            /**
             * Api Key Masked
             * @description 打码后的 API Key。明文不出现在任何响应中。
             * @default
             */
            api_key_masked: string;
            /**
             * Bound Lecture Ids
             * @default []
             */
            bound_lecture_ids: string[];
            /** Class Id */
            class_id: string;
            /**
             * Icon
             * @default
             */
            icon: string;
            /** Id */
            id: string;
            /**
             * Mcp Servers
             * @default []
             */
            mcp_servers: components["schemas"]["McpServerRead"][];
            /** Name */
            name: string;
            /**
             * Prompt
             * @default
             */
            prompt: string;
            /**
             * Skills
             * @default []
             */
            skills: components["schemas"]["SkillRead"][];
            /** Subject */
            subject: string;
        };
        /** AssistantUpdate */
        AssistantUpdate: {
            /** Bound Lecture Ids */
            bound_lecture_ids?: string[] | null;
            /** Prompt */
            prompt?: string | null;
        };
        /** AuditLogRead */
        AuditLogRead: {
            /** Action */
            action: string;
            /**
             * At
             * Format: date-time
             */
            at: string;
            /** Class Id */
            class_id: string;
            /**
             * Cost Ms
             * @default 0
             */
            cost_ms: number;
            /** Id */
            id: string;
            /**
             * Params
             * @default
             */
            params: string;
            /** Skill Key */
            skill_key?: string | null;
            status: components["schemas"]["AuditStatus"];
            /**
             * Tokens
             * @default 0
             */
            tokens: number;
            /** User Id */
            user_id: string;
            /** User Name */
            user_name: string;
        };
        /** AuditStats */
        AuditStats: {
            /** By Skill */
            by_skill: components["schemas"]["SkillBreakdown"][];
            /** Fail Rate */
            fail_rate: number;
            /** Total Calls */
            total_calls: number;
            /** Total Tokens */
            total_tokens: number;
        };
        /**
         * AuditStatus
         * @enum {string}
         */
        AuditStatus: "ok" | "failed";
        /** Body_import_skill_api_assistants__assistant_id__skills_import_post */
        Body_import_skill_api_assistants__assistant_id__skills_import_post: {
            /** File */
            file: string;
        };
        /** Body_upload_lecture_api_lectures_post */
        Body_upload_lecture_api_lectures_post: {
            /** File */
            file: string;
            /** Subject */
            subject: string;
            /** Title */
            title: string;
        };
        /** CareMessageCreate */
        CareMessageCreate: {
            /** Content */
            content: string;
        };
        /** CareMessageRead */
        CareMessageRead: {
            /** Content */
            content: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Emotion */
            emotion?: string | null;
            /** Id */
            id: string;
            role: components["schemas"]["MessageRole"];
        };
        /** CareReply */
        CareReply: {
            /** Emotion */
            emotion: string;
            /**
             * Escalated
             * @default false
             */
            escalated: boolean;
            /** Reply */
            reply: string;
        };
        /**
         * ChatDeltaEvent
         * @description SSE `delta` 事件载荷：一段回答文本增量。
         */
        ChatDeltaEvent: {
            /** Text */
            text: string;
        };
        /**
         * ChatDoneEvent
         * @description SSE `done` 事件载荷：结束标记，携带最终消息标识与来源引用。
         */
        ChatDoneEvent: {
            /**
             * Cost Ms
             * @default 0
             */
            cost_ms: number;
            /** Message Id */
            message_id: string;
            /** Skill Key */
            skill_key?: string | null;
            /**
             * Sources
             * @default []
             */
            sources: components["schemas"]["SourceRef"][];
            /**
             * Tokens
             * @default 0
             */
            tokens: number;
        };
        /**
         * ChatErrorEvent
         * @description SSE `error` 事件载荷：生成过程失败，流就此终止。
         */
        ChatErrorEvent: {
            /** Detail */
            detail: string;
        };
        /**
         * ChatTraceEvent
         * @description SSE `trace` 事件载荷：一步执行过程。
         */
        ChatTraceEvent: {
            /**
             * Detail
             * @default
             */
            detail: string;
            /** Icon */
            icon: string;
            /** Label */
            label: string;
        };
        /** ClassAnalytics */
        ClassAnalytics: {
            /**
             * Activity
             * @description [演示数据] 近七日活跃度
             */
            activity: number[];
            /** Overall */
            overall: number;
            /**
             * Skill Calls
             * @description 技能调用总次数，取自真实审计记录
             */
            skill_calls: number;
            /**
             * Student Count
             * @description 真实值
             */
            student_count: number;
            /** Topics */
            topics: components["schemas"]["TopicScore"][];
        };
        /** ClassRead */
        ClassRead: {
            /** Id */
            id: string;
            /** Name */
            name: string;
        };
        /** ConversationCreate */
        ConversationCreate: {
            /** Assistant Id */
            assistant_id: string;
        };
        /** ConversationRead */
        ConversationRead: {
            /** Assistant Id */
            assistant_id: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Id */
            id: string;
            /**
             * Messages
             * @default []
             */
            messages: components["schemas"]["MessageRead"][];
            /** User Id */
            user_id: string;
        };
        /** HomeworkCreate */
        HomeworkCreate: {
            /**
             * Description
             * @default
             */
            description: string;
            /** Due At */
            due_at?: string | null;
            /** @default published */
            state: components["schemas"]["HomeworkState"];
            /** Subject */
            subject: string;
            /** Title */
            title: string;
        };
        /** HomeworkRead */
        HomeworkRead: {
            /** Class Id */
            class_id: string;
            /**
             * Description
             * @default
             */
            description: string;
            /** Due At */
            due_at?: string | null;
            /** Id */
            id: string;
            my_submission?: components["schemas"]["SubmissionRead"] | null;
            state: components["schemas"]["HomeworkState"];
            /** Subject */
            subject: string;
            /**
             * Submission Count
             * @default 0
             */
            submission_count: number;
            /** Title */
            title: string;
        };
        /**
         * HomeworkState
         * @enum {string}
         */
        HomeworkState: "draft" | "published";
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** KbChunkRead */
        KbChunkRead: {
            /** Id */
            id: string;
            /**
             * Keywords
             * @default []
             */
            keywords: string[];
            /** Lecture Id */
            lecture_id: string;
            /**
             * Lecture Title
             * @default
             */
            lecture_title: string;
            /** Location */
            location: string;
            /** Subject */
            subject: string;
            /** Text */
            text: string;
        };
        /** KbSearchHit */
        KbSearchHit: {
            /** Id */
            id: string;
            /**
             * Keywords
             * @default []
             */
            keywords: string[];
            /** Lecture Id */
            lecture_id: string;
            /**
             * Lecture Title
             * @default
             */
            lecture_title: string;
            /** Location */
            location: string;
            /**
             * Score
             * @description 相关度，降序排列
             */
            score: number;
            /** Subject */
            subject: string;
            /** Text */
            text: string;
        };
        /** KbSearchResult */
        KbSearchResult: {
            /** Hits */
            hits: components["schemas"]["KbSearchHit"][];
            /** Query */
            query: string;
            /** Subject */
            subject?: string | null;
        };
        /** LearnerProfile */
        LearnerProfile: {
            /**
             * Strengths
             * @default []
             */
            strengths: string[];
            /**
             * Style
             * @description [演示数据] 学习风格
             */
            style: string;
            /**
             * Suggestion
             * @default
             */
            suggestion: string;
            /**
             * Tags
             * @default []
             */
            tags: string[];
            /**
             * Weaknesses
             * @default []
             */
            weaknesses: string[];
        };
        /** LectureRead */
        LectureRead: {
            /**
             * Chunk Count
             * @default 0
             */
            chunk_count: number;
            /** Class Id */
            class_id: string;
            /** Id */
            id: string;
            /** Subject */
            subject: string;
            /** Title */
            title: string;
            /**
             * Uploaded At
             * Format: date-time
             */
            uploaded_at: string;
            /**
             * Uploader
             * @default
             */
            uploader: string;
        };
        /** LoginRequest */
        LoginRequest: {
            /**
             * User Id
             * @description 账号标识。演示用登录，不校验密码。
             */
            user_id: string;
        };
        /** LoginResponse */
        LoginResponse: {
            /** Access Token */
            access_token: string;
            /**
             * Token Type
             * @default bearer
             */
            token_type: string;
            user: components["schemas"]["UserRead"];
        };
        /** McpServerCreate */
        McpServerCreate: {
            /** Name */
            name: string;
            /** Url */
            url: string;
        };
        /** McpServerRead */
        McpServerRead: {
            /**
             * Builtin
             * @default false
             */
            builtin: boolean;
            /** Id */
            id: string;
            /** Name */
            name: string;
            status: components["schemas"]["McpStatus"];
            /**
             * Tools
             * @default []
             */
            tools: string[];
            /** Url */
            url: string;
        };
        /**
         * McpStatus
         * @enum {string}
         */
        McpStatus: "connected" | "disconnected";
        /** MeRead */
        MeRead: {
            class: components["schemas"]["ClassRead"];
            /** Subjects */
            subjects: components["schemas"]["SubjectRead"][];
            user: components["schemas"]["UserRead"];
        };
        /** MessageCreate */
        MessageCreate: {
            /** Content */
            content: string;
        };
        /** MessageRead */
        MessageRead: {
            /** Content */
            content: string;
            /** Conversation Id */
            conversation_id: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Id */
            id: string;
            role: components["schemas"]["MessageRole"];
            /** Skill Key */
            skill_key?: string | null;
            /**
             * Sources
             * @default []
             */
            sources: components["schemas"]["SourceRef"][];
            /**
             * Trace
             * @default []
             */
            trace: components["schemas"]["TraceStep"][];
        };
        /**
         * MessageRole
         * @enum {string}
         */
        MessageRole: "user" | "assistant";
        /** MistakeExplainResult */
        MistakeExplainResult: {
            /**
             * Cached
             * @default false
             */
            cached: boolean;
            /** Explanation */
            explanation: string;
            /** Mistake Id */
            mistake_id: string;
            /**
             * Sources
             * @default []
             */
            sources: components["schemas"]["SourceRef"][];
        };
        /** MistakeRead */
        MistakeRead: {
            /** Explanation */
            explanation?: string | null;
            /**
             * Explanation Sources
             * @default []
             */
            explanation_sources: components["schemas"]["SourceRef"][];
            /** Homework Title */
            homework_title: string;
            /** Id */
            id: string;
            /** Question */
            question: string;
            /** Reason */
            reason: string;
            /** Student Answer */
            student_answer: string;
            /** Student Id */
            student_id: string;
            /**
             * Subject
             * @default
             */
            subject: string;
        };
        /** Page[AuditLogRead] */
        Page_AuditLogRead_: {
            /** Items */
            items: components["schemas"]["AuditLogRead"][];
            /**
             * Page
             * @default 1
             */
            page: number;
            /**
             * Page Size
             * @default 20
             */
            page_size: number;
            /** Total */
            total: number;
        };
        /**
         * Role
         * @enum {string}
         */
        Role: "teacher" | "student";
        /** SkillBreakdown */
        SkillBreakdown: {
            /** Calls */
            calls: number;
            /** Failures */
            failures: number;
            /** Skill Key */
            skill_key: string;
            /** Tokens */
            tokens: number;
        };
        /** SkillCreate */
        SkillCreate: {
            /**
             * Behavior
             * @default
             */
            behavior: string;
            /**
             * Enabled
             * @default true
             */
            enabled: boolean;
            /** Name */
            name: string;
            /**
             * Tools
             * @default []
             */
            tools: string[];
            /**
             * When
             * @default
             */
            when: string;
        };
        /**
         * SkillImportPreview
         * @description 技能包解析结果。未找到清单时 manifest_found 为 false，需人工补全。
         */
        SkillImportPreview: {
            /**
             * Behavior
             * @default
             */
            behavior: string;
            /**
             * Entries
             * @description 包内文件清单
             * @default []
             */
            entries: string[];
            /** Manifest Found */
            manifest_found: boolean;
            /**
             * Name
             * @default
             */
            name: string;
            /**
             * Note
             * @default
             */
            note: string;
            /**
             * Tools
             * @default []
             */
            tools: string[];
            /**
             * When
             * @default
             */
            when: string;
        };
        /** SkillRead */
        SkillRead: {
            /** Behavior */
            behavior: string;
            /** Enabled */
            enabled: boolean;
            /** Id */
            id: string;
            /** Key */
            key: string;
            /** Name */
            name: string;
            /** Required */
            required: boolean;
            /**
             * Tools
             * @default []
             */
            tools: string[];
            /** When */
            when: string;
        };
        /** SkillUpdate */
        SkillUpdate: {
            /** Behavior */
            behavior?: string | null;
            /** Enabled */
            enabled?: boolean | null;
            /** Name */
            name?: string | null;
            /** Tools */
            tools?: string[] | null;
            /** When */
            when?: string | null;
        };
        /**
         * SourceRef
         * @description 回答/评语的来源引用。
         */
        SourceRef: {
            /** Lecture Title */
            lecture_title: string;
            /** Location */
            location: string;
            /**
             * Text
             * @default
             */
            text: string;
        };
        /** StudentAnalytics */
        StudentAnalytics: {
            /** Overall */
            overall: number;
            profile: components["schemas"]["LearnerProfile"];
            /**
             * Progress
             * @description [演示数据] 历史段 + 真实已批改分数
             */
            progress: number[];
            stats: components["schemas"]["StudentStats"];
            /** Topics */
            topics: components["schemas"]["TopicScore"][];
        };
        /** StudentDashboard */
        StudentDashboard: {
            /** Class Id */
            class_id: string;
            /** Class Name */
            class_name: string;
            /** Homework Count */
            homework_count: number;
            /** Lecture Count */
            lecture_count: number;
            /** Mistake Count */
            mistake_count: number;
            /** Subjects */
            subjects: string[];
            /** Unsubmitted Count */
            unsubmitted_count: number;
        };
        /** StudentStats */
        StudentStats: {
            /**
             * Accuracy
             * @description 正确率百分比，真实值
             */
            accuracy: number;
            /**
             * Mistakes
             * @description 错题数，真实值
             */
            mistakes: number;
            /**
             * Questions
             * @description 提问次数，取自真实审计记录
             */
            questions: number;
            /**
             * Submissions
             * @description 提交份数，真实值
             */
            submissions: number;
        };
        /** SubjectRead */
        SubjectRead: {
            /**
             * Icon
             * @default
             */
            icon: string;
            /** Subject */
            subject: string;
        };
        /** SubmissionCreate */
        SubmissionCreate: {
            /** Content */
            content: string;
        };
        /** SubmissionRead */
        SubmissionRead: {
            /** Ai Basis */
            ai_basis?: string | null;
            /** Ai Comment */
            ai_comment?: string | null;
            /** Ai Score */
            ai_score?: number | null;
            /** Content */
            content: string;
            /** Homework Id */
            homework_id: string;
            /** Id */
            id: string;
            /** Overridden At */
            overridden_at?: string | null;
            state: components["schemas"]["SubmissionState"];
            /** Student Id */
            student_id: string;
            /**
             * Student Name
             * @default
             */
            student_name: string;
            /**
             * Submitted At
             * Format: date-time
             */
            submitted_at: string;
            /** Teacher Comment */
            teacher_comment?: string | null;
            /** Teacher Score */
            teacher_score?: number | null;
            /**
             * Wrong
             * @default false
             */
            wrong: boolean;
        };
        /**
         * SubmissionReview
         * @description 教师终评。覆盖展示，但不抹除 AI 原始评分。
         */
        SubmissionReview: {
            /**
             * Teacher Comment
             * @default
             */
            teacher_comment: string;
            /** Teacher Score */
            teacher_score: number;
        };
        /**
         * SubmissionState
         * @enum {string}
         */
        SubmissionState: "submitted" | "grading" | "graded";
        /** TeacherDashboard */
        TeacherDashboard: {
            analytics: components["schemas"]["ClassAnalytics"];
            /** Class Id */
            class_id: string;
            /** Class Name */
            class_name: string;
            /** Homework Count */
            homework_count: number;
            /** Lecture Count */
            lecture_count: number;
            /** Pending Submissions */
            pending_submissions: number;
            /** Subjects */
            subjects: string[];
        };
        /** TopicScore */
        TopicScore: {
            /** Label */
            label: string;
            /**
             * Value
             * @description [演示数据] 学科掌握度基准值
             */
            value: number;
        };
        /**
         * TraceStep
         * @description AI 执行过程中的一步。
         */
        TraceStep: {
            /**
             * Detail
             * @default
             */
            detail: string;
            /** Icon */
            icon: string;
            /** Label */
            label: string;
        };
        /**
         * UserRead
         * @description 账号信息。MUST NOT 含任何凭据字段。
         */
        UserRead: {
            /**
             * Avatar
             * @default
             */
            avatar: string;
            /** Class Id */
            class_id: string;
            /**
             * Class Name
             * @default
             */
            class_name: string;
            /** Id */
            id: string;
            /** Name */
            name: string;
            role: components["schemas"]["Role"];
        };
        /** ValidationError */
        ValidationError: {
            /** Context */
            ctx?: Record<string, never>;
            /** Input */
            input?: unknown;
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    class_stats_api_analytics_class_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ClassAnalytics"];
                };
            };
        };
    };
    my_analytics_api_analytics_student_me_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StudentAnalytics"];
                };
            };
        };
    };
    list_assistants_api_assistants_get: {
        parameters: {
            query?: {
                subject?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssistantRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_assistant_api_assistants__assistant_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                assistant_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssistantRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_assistant_api_assistants__assistant_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                assistant_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AssistantUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssistantRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_mcp_servers_api_assistants__assistant_id__mcp_servers_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                assistant_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["McpServerRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    add_mcp_server_api_assistants__assistant_id__mcp_servers_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                assistant_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["McpServerCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["McpServerRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_mcp_server_api_assistants__assistant_id__mcp_servers__server_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                assistant_id: string;
                server_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_skills_api_assistants__assistant_id__skills_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                assistant_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SkillRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_skill_api_assistants__assistant_id__skills_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                assistant_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SkillCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SkillRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_skill_api_assistants__assistant_id__skills__skill_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                assistant_id: string;
                skill_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_skill_api_assistants__assistant_id__skills__skill_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                assistant_id: string;
                skill_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SkillUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SkillRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    import_skill_api_assistants__assistant_id__skills_import_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                assistant_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_import_skill_api_assistants__assistant_id__skills_import_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SkillImportPreview"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_logs_api_audit_logs_get: {
        parameters: {
            query?: {
                page?: number;
                page_size?: number;
                skill_key?: string | null;
                status?: components["schemas"]["AuditStatus"] | null;
                user_id?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_AuditLogRead_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    read_stats_api_audit_stats_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuditStats"];
                };
            };
        };
    };
    login_api_auth_login_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LoginRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LoginResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    read_me_api_auth_me_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MeRead"];
                };
            };
        };
    };
    my_care_messages_api_care_messages_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CareMessageRead"][];
                };
            };
        };
    };
    send_care_message_api_care_messages_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CareMessageCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CareReply"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    ensure_conversation_api_conversations_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ConversationCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConversationRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_messages_api_conversations__conversation_id__messages_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                conversation_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MessageRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    send_message_api_conversations__conversation_id__messages_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                conversation_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MessageCreate"];
            };
        };
        responses: {
            /** @description SSE 事件流。每个事件的 `data` 为下列载荷之一。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "text/event-stream": string | components["schemas"]["ChatTraceEvent"] | components["schemas"]["ChatDeltaEvent"] | components["schemas"]["ChatDoneEvent"] | components["schemas"]["ChatErrorEvent"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    student_dashboard_api_dashboard_student_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StudentDashboard"];
                };
            };
        };
    };
    teacher_dashboard_api_dashboard_teacher_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TeacherDashboard"];
                };
            };
        };
    };
    list_homeworks_api_homeworks_get: {
        parameters: {
            query?: {
                subject?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HomeworkRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_homework_api_homeworks_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["HomeworkCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HomeworkRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_submissions_api_homeworks__homework_id__submissions_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                homework_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SubmissionRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    submit_api_homeworks__homework_id__submissions_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                homework_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SubmissionCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SubmissionRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    search_kb_api_kb_search_get: {
        parameters: {
            query: {
                limit?: number;
                /** @description 检索词 */
                q: string;
                subject?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["KbSearchResult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_lectures_api_lectures_get: {
        parameters: {
            query?: {
                /** @description 按学科过滤 */
                subject?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LectureRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    upload_lecture_api_lectures_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_upload_lecture_api_lectures_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LectureRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_lecture_api_lectures__lecture_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                lecture_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_chunks_api_lectures__lecture_id__chunks_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                lecture_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["KbChunkRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    explain_api_mistakes__mistake_id__explain_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                mistake_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MistakeExplainResult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    my_mistakes_api_mistakes_mine_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MistakeRead"][];
                };
            };
        };
    };
    get_submission_api_submissions__submission_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                submission_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SubmissionRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    review_api_submissions__submission_id__review_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                submission_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SubmissionReview"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SubmissionRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    my_submissions_api_submissions_mine_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SubmissionRead"][];
                };
            };
        };
    };
    list_users_api_users_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserRead"][];
                };
            };
        };
    };
    health_health_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: string;
                    };
                };
            };
        };
    };
}
