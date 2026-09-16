"use client";

/** 知识库检索：在本班知识块中按关键词匹配，结果标明讲义标题与位置。 */

import { useState } from "react";

import { apiGet } from "@/lib/api";
import type { Res } from "@/lib/api";
import { errorMessage, useSession } from "@/lib/session";
import { Empty, ErrorBanner, PageHead, SubjectFilter } from "@/components/ui";

type SearchResult = Res<"/api/kb/search">;

export default function StudentKbPage() {
  const { me } = useSession();
  const subjects = (me?.subjects ?? []).map((s) => s.subject);

  const [q, setQ] = useState("");
  const [subject, setSubject] = useState("");
  const [result, setResult] = useState<SearchResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function search() {
    if (!q.trim()) return;
    setBusy(true);
    setError(null);
    try {
      setResult(await apiGet("/api/kb/search", { query: { q, subject: subject || undefined } }));
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHead title="知识库检索" desc="只检索本班讲义切分出的知识块，其他班级的内容不会出现在结果中。" />
      <ErrorBanner error={error} />

      <div className="card">
        <div className="row">
          <input
            style={{ flex: 1, minWidth: 220 }}
            value={q}
            placeholder="输入关键词，如：单调性、摩尔质量"
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && search()}
          />
          <SubjectFilter subjects={subjects} value={subject} onChange={setSubject} />
          <button className="primary" disabled={busy || !q.trim()} onClick={search}>
            {busy ? "检索中…" : "检索"}
          </button>
        </div>
      </div>

      {result ? (
        <div className="card" style={{ marginTop: 14 }}>
          <h3>
            「{result.query}」的结果 · {result.hits.length} 条
            {result.subject ? <span className="tag brand" style={{ marginLeft: 8 }}>{result.subject}</span> : null}
          </h3>
          {result.hits.length === 0 ? (
            <Empty>未检索到相关内容。可以换个说法，或请教师上传相关讲义。</Empty>
          ) : (
            <div className="col">
              {result.hits.map((h) => (
                <div key={h.id} className="card" style={{ background: "var(--surface-2)" }}>
                  <div className="row small muted">
                    <span className="tag brand">{h.subject}</span>
                    <b>{h.lecture_title}</b>
                    <span className="tag">{h.location}</span>
                    <div className="spacer" />
                    <span>相关度 {h.score.toFixed(2)}</span>
                  </div>
                  <div style={{ marginTop: 6 }}>{h.text}</div>
                  <div className="row small muted" style={{ marginTop: 6 }}>
                    {h.keywords.map((k) => (
                      <span key={k} className="tag">
                        {k}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : null}
    </>
  );
}
