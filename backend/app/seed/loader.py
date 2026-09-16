"""种子数据加载。

数据来自 app/seed/data.json，由 scripts/extract_seed.mjs 从演示 bundle 提取。
加载是幂等的：仅当数据库为空时执行。

插入顺序按依赖分组并逐组 flush —— SQLAlchemy 的 unit-of-work 按 ORM
relationship 排序，裸外键列不参与排序，因此父表必须先落库。
"""

import json
from datetime import datetime
from pathlib import Path

from sqlmodel import Session, func, select

from app.models import (
    Assistant,
    AuditLog,
    AuditStatus,
    Class,
    Homework,
    HomeworkState,
    KbChunk,
    Lecture,
    McpServer,
    McpStatus,
    Mistake,
    Role,
    Skill,
    Submission,
    SubmissionState,
    User,
)

DATA_PATH = Path(__file__).resolve().parent / "data.json"


def _dt(value: str | None) -> datetime | None:
    """演示数据的时间是 'YYYY-MM-DD HH:MM' 形式。"""
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d %H:%M")


def load_seed_data() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def is_empty(session: Session) -> bool:
    return session.exec(select(func.count()).select_from(Class)).one() == 0


def seed(session: Session) -> dict[str, int]:
    """写入种子数据，返回各实体写入行数。调用方需自行保证数据库为空。"""
    raw = load_seed_data()
    counts: dict[str, int] = {}

    def add(group: list, key: str) -> None:
        session.add_all(group)
        session.flush()
        counts[key] = len(group)

    add([Class(id=c["id"], name=c["name"]) for c in raw["classes"]], "classes")

    add(
        [
            User(
                id=u["id"],
                name=u["name"],
                role=Role(u["role"]),
                class_id=u["classId"],
                avatar=u.get("avatar", ""),
            )
            for u in raw["users"]
        ],
        "users",
    )

    # 演示 bundle 里 uploader 存的是用户标识；模型中它是展示用的姓名
    # （上传接口写入的也是姓名），在此处统一，避免界面上出现裸 id
    user_names = {u["id"]: u["name"] for u in raw["users"]}

    add(
        [
            Lecture(
                id=lec["id"],
                class_id=lec["classId"],
                subject=lec["subject"],
                title=lec["title"],
                uploader=user_names.get(lec.get("uploader", ""), lec.get("uploader", "")),
                uploaded_at=_dt(lec.get("uploadedAt")) or datetime.now(),
            )
            for lec in raw["lectures"]
        ],
        "lectures",
    )

    add(
        [
            Assistant(
                id=a["id"],
                class_id=a["classId"],
                subject=a["subject"],
                name=a["name"],
                icon=a.get("icon", ""),
                prompt=a.get("prompt", ""),
                api_key=a.get("apiKey", ""),
                bound_lecture_ids=a.get("boundLectureIds", []),
            )
            for a in raw["assistants"]
        ],
        "assistants",
    )

    add(
        [
            Homework(
                id=h["id"],
                class_id=h["classId"],
                subject=h["subject"],
                title=h["title"],
                description=h.get("description", ""),
                state=HomeworkState(h.get("state", "published")),
                due_at=_dt(h.get("dueAt")),
            )
            for h in raw["homeworks"]
        ],
        "homeworks",
    )

    add(
        [
            KbChunk(
                id=c["id"],
                lecture_id=c["lectureId"],
                class_id=c["classId"],
                subject=c["subject"],
                location=c["location"],
                keywords=c.get("keywords", []),
                text=c["text"],
                order_index=index,
            )
            for index, c in enumerate(raw["kbChunks"])
        ],
        "kb_chunks",
    )

    skills: list[Skill] = []
    servers: list[McpServer] = []
    for a in raw["assistants"]:
        for s in a.get("skills", []):
            skills.append(
                Skill(
                    id=f"{a['id']}::{s['id']}",
                    assistant_id=a["id"],
                    key=s["id"],
                    name=s["name"],
                    when=s.get("when", ""),
                    behavior=s.get("behavior", ""),
                    enabled=s.get("enabled", True),
                    required=s.get("required", False),
                    tools=s.get("tools", []),
                )
            )
        for m in a.get("mcpServers", []):
            servers.append(
                McpServer(
                    id=f"{a['id']}::{m['id']}",
                    assistant_id=a["id"],
                    name=m["name"],
                    url=m["url"],
                    status=McpStatus(m.get("status", "connected")),
                    tools=m.get("tools", []),
                    builtin=m.get("builtin", False),
                )
            )
    add(skills, "skills")
    add(servers, "mcp_servers")

    homework_subject = {h["id"]: h["subject"] for h in raw["homeworks"]}
    homework_title = {h["id"]: h["title"] for h in raw["homeworks"]}

    add(
        [
            Submission(
                id=s["id"],
                homework_id=s["homeworkId"],
                student_id=s["studentId"],
                content=s["content"],
                submitted_at=_dt(s.get("submittedAt")) or datetime.now(),
                state=SubmissionState(s.get("state", "submitted")),
                ai_score=s.get("aiScore"),
                ai_comment=s.get("aiComment"),
                ai_basis=s.get("aiBasis"),
                wrong=s.get("wrong", False),
                teacher_score=s.get("teacherScore"),
                teacher_comment=s.get("teacherComment"),
                overridden_at=_dt(s.get("overriddenAt")),
            )
            for s in raw["submissions"]
        ],
        "submissions",
    )

    title_to_subject = {t: homework_subject[hid] for hid, t in homework_title.items()}
    add(
        [
            Mistake(
                id=m["id"],
                student_id=m["studentId"],
                submission_id=m.get("submissionId"),
                subject=title_to_subject.get(m["homeworkTitle"], ""),
                homework_title=m["homeworkTitle"],
                question=m["question"],
                student_answer=m["studentAnswer"],
                reason=m["reason"],
                explanation=m.get("explanation"),
            )
            for m in raw["mistakes"]
        ],
        "mistakes",
    )

    add(
        [
            AuditLog(
                id=log["id"],
                at=_dt(log.get("at")) or datetime.now(),
                user_id=log["userId"],
                user_name=log["userName"],
                class_id=log["classId"],
                skill_key=log.get("skillId"),
                action=log["action"],
                params=log.get("params", ""),
                status=AuditStatus(log.get("status", "ok")),
                cost_ms=log.get("costMs", 0),
                tokens=log.get("tokens", 0),
            )
            for log in raw["auditLogs"]
        ],
        "audit_logs",
    )

    session.commit()
    return counts


def seed_if_empty(session: Session) -> dict[str, int] | None:
    """数据库为空时执行 seed，否则跳过。"""
    if not is_empty(session):
        return None
    return seed(session)
