"use client";

/** 错题本：来自批改判错的记录，可按错因请求讲解（讲解持久化，重复请求不重复计 token）。 */

import { useCallback, useEffect, useState } from "react";

import { apiGet, apiPost } from "@/lib/api";
import type { Res } from "@/lib/api";
import { errorMessage } from "@/lib/session";
import { Empty, ErrorBanner, Loading, PageHead } from "@/components/ui";

type Mistake = Res<"/api/mistakes/mine">[number];

export default function StudentMistakesPage() {
  const [rows, setRows] = useState<Mistake[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(() => {
    apiGet("/api/mistakes/mine").then(setRows).catch((e) => setError(errorMessage(e)));
  }, []);

  useEffect(load, [load]);

  async function explain(id: string) {
    setBusyId(id);
    setError(null);
    try {
      const res = await apiPost("/api/mistakes/{mistake_id}/explain", undefined, {
        path: { mistake_id: id },
      });
      setRows(
        (prev) =>
          prev?.map((m) =>
            m.id === id
              ? { ...m, explanation: res.explanation, explanation_sources: res.sources }
              : m,
          ) ?? null,
      );
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <>
      <PageHead title="错题本" desc="讲解针对错因说明思路偏差，默认不直接给最终答案。" />
      <ErrorBanner error={error} />

      {rows === null ? (
        <Loading />
      ) : rows.length === 0 ? (
        <Empty>还没有错题。作业被判错时会自动出现在这里。</Empty>
      ) : (
        <div className="col" style={{ gap: 14 }}>
          {rows.map((m) => (
            <div key={m.id} className="card">
              <div className="row">
                <b>{m.homework_title}</b>
                {m.subject ? <span className="tag brand">{m.subject}</span> : null}
              </div>

              <div className="small" style={{ marginTop: 8 }}>
                <div className="muted">题目</div>
                <div>{m.question}</div>
              </div>
              <div className="small" style={{ marginTop: 8 }}>
                <div className="muted">我的作答</div>
                <div>{m.student_answer}</div>
              </div>
              <div className="small" style={{ marginTop: 8 }}>
                <div className="muted">错因</div>
                <div>{m.reason}</div>
              </div>

              {m.explanation ? (
                <div className="card" style={{ marginTop: 10, background: "var(--surface-2)" }}>
                  <div className="small muted">讲解</div>
                  <div style={{ whiteSpace: "pre-wrap" }}>{m.explanation}</div>
                  {m.explanation_sources.length ? (
                    <div className="sources">
                      <div className="muted" style={{ marginBottom: 4 }}>
                        来源引用
                      </div>
                      {m.explanation_sources.map((s, i) => (
                        <div key={i}>
                          <span className="tag">{s.lecture_title}</span>{" "}
                          <span className="muted">{s.location}</span>
                        </div>
                      ))}
                    </div>
                  ) : null}
                </div>
              ) : (
                <button
                  className="primary"
                  style={{ marginTop: 10 }}
                  disabled={busyId === m.id}
                  onClick={() => explain(m.id)}
                >
                  {busyId === m.id ? "生成中…" : "请求讲解"}
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </>
  );
}
