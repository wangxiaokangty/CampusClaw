"use client";

/**
 * 我的作业：提交后轮询 `GET /submissions/{id}`，界面上能看到
 * 「已提交 → 批改中 → 已批改」的过渡（design.md D6）。
 */

import { useCallback, useEffect, useRef, useState } from "react";

import { apiGet, apiPost } from "@/lib/api";
import type { Res } from "@/lib/api";
import { errorMessage, useSession } from "@/lib/session";
import { Empty, ErrorBanner, Loading, PageHead, SubjectFilter } from "@/components/ui";
import { StateTag } from "@/components/submission";

type Homework = Res<"/api/homeworks">[number];
type Submission = Res<"/api/submissions/{submission_id}">;

const POLL_MS = 1000;

export default function StudentHomeworkPage() {
  const { me } = useSession();
  const subjects = (me?.subjects ?? []).map((s) => s.subject);

  const [subject, setSubject] = useState("");
  const [homeworks, setHomeworks] = useState<Homework[] | null>(null);
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
        title="我的作业"
        desc="提交后由 AI 异步批改；判错的题会自动进入错题本。看不到其他同学的提交。"
        actions={<SubjectFilter subjects={subjects} value={subject} onChange={setSubject} />}
      />
      <ErrorBanner error={error} />

      {homeworks === null ? (
        <Loading />
      ) : homeworks.length === 0 ? (
        <Empty>该筛选条件下暂无作业</Empty>
      ) : (
        <div className="col" style={{ gap: 14 }}>
          {homeworks.map((h) => (
            <HomeworkCard key={h.id} homework={h} onError={setError} />
          ))}
        </div>
      )}
    </>
  );
}

function HomeworkCard({
  homework,
  onError,
}: {
  homework: Homework;
  onError: (m: string | null) => void;
}) {
  const [submission, setSubmission] = useState<Submission | null>(
    (homework.my_submission as Submission | null) ?? null,
  );
  const [draft, setDraft] = useState(homework.my_submission?.content ?? "");
  const [busy, setBusy] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // 未进入「已批改」前持续轮询，直到状态收敛
  useEffect(() => {
    if (!submission || submission.state === "graded") return;
    timer.current = setTimeout(async () => {
      try {
        setSubmission(
          await apiGet("/api/submissions/{submission_id}", {
            path: { submission_id: submission.id },
          }),
        );
      } catch (e) {
        onError(errorMessage(e));
      }
    }, POLL_MS);
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, [submission, onError]);

  async function submit() {
    if (!draft.trim()) return;
    setBusy(true);
    onError(null);
    try {
      setSubmission(
        await apiPost(
          "/api/homeworks/{homework_id}/submissions",
          { content: draft },
          { path: { homework_id: homework.id } },
        ),
      );
    } catch (e) {
      onError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  const finalScore = submission?.teacher_score ?? submission?.ai_score ?? null;

  return (
    <div className="card">
      <div className="row">
        <div>
          <b>{homework.title}</b>
          <div className="small muted">{homework.description}</div>
        </div>
        <div className="spacer" />
        <span className="tag brand">{homework.subject}</span>
        {homework.due_at ? (
          <span className="small muted">
            截止 {new Date(homework.due_at).toLocaleDateString("zh-CN")}
          </span>
        ) : null}
        {submission ? <StateTag state={submission.state} /> : <span className="tag">未提交</span>}
      </div>

      <label className="field" style={{ marginTop: 12 }}>
        <span>我的作答</span>
        <textarea rows={3} value={draft} onChange={(e) => setDraft(e.target.value)} />
      </label>
      <button className="primary" disabled={busy || !draft.trim()} onClick={submit}>
        {busy ? "提交中…" : submission ? "重新提交（覆盖）" : "提交"}
      </button>

      {submission && submission.state !== "graded" ? (
        <p className="small muted" style={{ marginBottom: 0 }}>
          {submission.state === "submitted" ? "已提交，等待批改…" : "AI 正在批改，稍候…"}
        </p>
      ) : null}

      {submission && submission.state === "graded" ? (
        <div className="card" style={{ marginTop: 12, background: "var(--surface-2)" }}>
          <div className="row">
            <span className="tag ok">最终得分 {finalScore}</span>
            {submission.teacher_score !== null ? (
              <span className="tag brand">教师终评</span>
            ) : (
              <span className="tag">AI 评分</span>
            )}
            {submission.wrong ? <span className="tag danger">已判错，见错题本</span> : null}
          </div>
          <div className="small" style={{ marginTop: 8 }}>
            {submission.teacher_comment || submission.ai_comment}
          </div>
          {submission.ai_basis ? (
            <div className="small muted" style={{ marginTop: 4 }}>
              评分依据：{submission.ai_basis}
            </div>
          ) : null}
          {submission.teacher_score !== null && submission.ai_score !== null ? (
            <div className="small muted" style={{ marginTop: 4 }}>
              AI 原始评分 {submission.ai_score}
              {submission.overridden_at
                ? ` · 教师于 ${new Date(submission.overridden_at).toLocaleString("zh-CN")} 覆盖`
                : ""}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
