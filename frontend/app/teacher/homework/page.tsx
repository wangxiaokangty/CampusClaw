"use client";

/** 作业与批改：发布作业、查看提交、覆盖终评（保留 AI 原始评分）。 */

import { useCallback, useEffect, useState } from "react";

import { apiGet, apiPatch, apiPost } from "@/lib/api";
import type { Res } from "@/lib/api";
import { errorMessage, useSession } from "@/lib/session";
import { Empty, ErrorBanner, Loading, PageHead, SubjectFilter } from "@/components/ui";
import { StateTag } from "@/components/submission";

type Homework = Res<"/api/homeworks">[number];
type Submission = Res<"/api/homeworks/{homework_id}/submissions">[number];

export default function TeacherHomeworkPage() {
  const { me } = useSession();
  const subjects = (me?.subjects ?? []).map((s) => s.subject);

  const [subject, setSubject] = useState("");
  const [homeworks, setHomeworks] = useState<Homework[] | null>(null);
  const [openId, setOpenId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    apiGet("/api/homeworks", { query: subject ? { subject } : {} })
      .then(setHomeworks)
      .catch((e) => setError(errorMessage(e)));
  }, [subject]);

  useEffect(load, [load]);

  return (
    <>
      <PageHead
        title="作业与批改"
        desc="学生提交后由 AI 异步批改，教师可覆盖终评；AI 原始评分保留可查。"
        actions={<SubjectFilter subjects={subjects} value={subject} onChange={setSubject} />}
      />
      <ErrorBanner error={error} />

      <PublishCard subjects={subjects} onPublished={load} onError={setError} />

      <div className="card" style={{ marginTop: 14 }}>
        <h3>本班作业</h3>
        {homeworks === null ? (
          <Loading />
        ) : homeworks.length === 0 ? (
          <Empty>该筛选条件下暂无作业</Empty>
        ) : (
          <table>
            <thead>
              <tr>
                <th>标题</th>
                <th>学科</th>
                <th>截止</th>
                <th>提交份数</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {homeworks.map((h) => (
                <tr key={h.id}>
                  <td>
                    <b>{h.title}</b>
                    <div className="small muted">{h.description}</div>
                    {openId === h.id ? <SubmissionList homeworkId={h.id} onError={setError} /> : null}
                  </td>
                  <td>
                    <span className="tag brand">{h.subject}</span>
                  </td>
                  <td className="small muted">
                    {h.due_at ? new Date(h.due_at).toLocaleDateString("zh-CN") : "—"}
                  </td>
                  <td>{h.submission_count}</td>
                  <td>
                    <button className="sm" onClick={() => setOpenId(openId === h.id ? null : h.id)}>
                      {openId === h.id ? "收起" : "查看提交"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}

function PublishCard({
  subjects,
  onPublished,
  onError,
}: {
  subjects: string[];
  onPublished: () => void;
  onError: (m: string | null) => void;
}) {
  const [form, setForm] = useState({ subject: "", title: "", description: "", due_at: "" });

  useEffect(() => {
    if (!form.subject && subjects.length) setForm((f) => ({ ...f, subject: subjects[0] }));
  }, [subjects, form.subject]);

  async function submit() {
    onError(null);
    try {
      await apiPost("/api/homeworks", {
        subject: form.subject,
        title: form.title,
        description: form.description,
        due_at: form.due_at ? new Date(form.due_at).toISOString() : null,
        state: "published",
      });
      setForm({ subject: form.subject, title: "", description: "", due_at: "" });
      onPublished();
    } catch (e) {
      onError(errorMessage(e));
    }
  }

  return (
    <div className="card">
      <h3>发布作业</h3>
      <div className="grid cols-3">
        <label className="field">
          <span>学科</span>
          <select value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })}>
            {subjects.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>标题</span>
          <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
        </label>
        <label className="field">
          <span>截止时间</span>
          <input
            type="date"
            value={form.due_at}
            onChange={(e) => setForm({ ...form, due_at: e.target.value })}
          />
        </label>
      </div>
      <label className="field">
        <span>描述 / 题面</span>
        <textarea
          rows={3}
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
        />
      </label>
      <button className="primary" disabled={!form.title || !form.subject} onClick={submit}>
        发布
      </button>
    </div>
  );
}

function SubmissionList({
  homeworkId,
  onError,
}: {
  homeworkId: string;
  onError: (m: string | null) => void;
}) {
  const [rows, setRows] = useState<Submission[] | null>(null);

  const load = useCallback(() => {
    apiGet("/api/homeworks/{homework_id}/submissions", { path: { homework_id: homeworkId } })
      .then(setRows)
      .catch((e) => onError(errorMessage(e)));
  }, [homeworkId, onError]);

  useEffect(load, [load]);

  if (rows === null) return <Loading />;
  if (!rows.length) return <div className="small muted" style={{ marginTop: 8 }}>尚无提交</div>;

  return (
    <div className="col" style={{ marginTop: 10, gap: 10 }}>
      {rows.map((s) => (
        <ReviewRow key={s.id} submission={s} onReviewed={load} onError={onError} />
      ))}
    </div>
  );
}

function ReviewRow({
  submission,
  onReviewed,
  onError,
}: {
  submission: Submission;
  onReviewed: () => void;
  onError: (m: string | null) => void;
}) {
  const [score, setScore] = useState(
    submission.teacher_score ?? submission.ai_score ?? 0,
  );
  const [comment, setComment] = useState(submission.teacher_comment ?? "");
  const [saving, setSaving] = useState(false);
  const gradable = submission.state === "graded";

  async function save() {
    setSaving(true);
    onError(null);
    try {
      await apiPatch(
        "/api/submissions/{submission_id}/review",
        { teacher_score: Number(score), teacher_comment: comment },
        { path: { submission_id: submission.id } },
      );
      onReviewed();
    } catch (e) {
      onError(errorMessage(e));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card" style={{ padding: 12 }}>
      <div className="row">
        <b>{submission.student_name || submission.student_id}</b>
        <StateTag state={submission.state} />
        <div className="spacer" />
        <span className="small muted">
          {new Date(submission.submitted_at).toLocaleString("zh-CN")}
        </span>
      </div>

      <div className="small" style={{ marginTop: 8, whiteSpace: "pre-wrap" }}>
        {submission.content}
      </div>

      {submission.ai_score !== null ? (
        <div className="card" style={{ marginTop: 10, padding: 10, background: "var(--surface-2)" }}>
          <div className="row small">
            <span className="tag brand">AI 评分 {submission.ai_score}</span>
            {submission.wrong ? <span className="tag danger">判错，已生成错题</span> : null}
          </div>
          <div className="small" style={{ marginTop: 6 }}>{submission.ai_comment}</div>
          {submission.ai_basis ? (
            <div className="small muted" style={{ marginTop: 4 }}>依据：{submission.ai_basis}</div>
          ) : null}
        </div>
      ) : null}

      <div className="row" style={{ marginTop: 10 }}>
        <input
          type="number"
          min={0}
          max={100}
          style={{ width: 88 }}
          value={score}
          disabled={!gradable}
          onChange={(e) => setScore(Number(e.target.value))}
        />
        <input
          placeholder="教师评语"
          value={comment}
          disabled={!gradable}
          onChange={(e) => setComment(e.target.value)}
          style={{ flex: 1, minWidth: 180 }}
        />
        <button className="primary" disabled={!gradable || saving} onClick={save}>
          {saving ? "保存中…" : "覆盖终评"}
        </button>
      </div>
      {!gradable ? (
        <p className="small muted" style={{ margin: "6px 0 0" }}>
          批改完成后才能改分。
        </p>
      ) : null}
      {submission.overridden_at ? (
        <p className="small muted" style={{ margin: "6px 0 0" }}>
          已于 {new Date(submission.overridden_at).toLocaleString("zh-CN")} 覆盖终评
        </p>
      ) : null}
    </div>
  );
}
