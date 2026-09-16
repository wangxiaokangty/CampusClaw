"use client";

/** 讲义与知识库：列表、按学科过滤、上传切块、删除（级联清理知识块与助手绑定）。 */

import { useCallback, useEffect, useState } from "react";

import { apiDelete, apiGet, apiUpload } from "@/lib/api";
import type { Res } from "@/lib/api";
import { errorMessage, useSession } from "@/lib/session";
import { Empty, ErrorBanner, Loading, PageHead, SubjectFilter } from "@/components/ui";

type Lecture = Res<"/api/lectures">[number];
type Chunk = Res<"/api/lectures/{lecture_id}/chunks">[number];

export default function TeacherLecturesPage() {
  const { me } = useSession();
  const subjects = (me?.subjects ?? []).map((s) => s.subject);

  const [subject, setSubject] = useState("");
  const [lectures, setLectures] = useState<Lecture[] | null>(null);
  const [openId, setOpenId] = useState<string | null>(null);
  const [chunks, setChunks] = useState<Chunk[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    apiGet("/api/lectures", { query: subject ? { subject } : {} })
      .then(setLectures)
      .catch((e) => setError(errorMessage(e)));
  }, [subject]);

  useEffect(load, [load]);

  async function openChunks(id: string) {
    if (openId === id) {
      setOpenId(null);
      setChunks(null);
      return;
    }
    setOpenId(id);
    setChunks(null);
    try {
      setChunks(await apiGet("/api/lectures/{lecture_id}/chunks", { path: { lecture_id: id } }));
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  async function remove(id: string) {
    setError(null);
    try {
      await apiDelete("/api/lectures/{lecture_id}", { path: { lecture_id: id } });
      if (openId === id) {
        setOpenId(null);
        setChunks(null);
      }
      load();
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  async function upload(form: FormData) {
    setBusy(true);
    setError(null);
    try {
      await apiUpload("/api/lectures", form);
      load();
      return true;
    } catch (e) {
      setError(errorMessage(e));
      return false;
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHead
        title="讲义与知识库"
        desc="讲义上传后自动切分为知识块，是助手回答与批改引用来源的唯一依据。"
        actions={<SubjectFilter subjects={subjects} value={subject} onChange={setSubject} />}
      />

      <ErrorBanner error={error} />

      <UploadCard subjects={subjects} busy={busy} onUpload={upload} />

      <div className="card" style={{ marginTop: 14 }}>
        <h3>本班讲义</h3>
        {lectures === null ? (
          <Loading />
        ) : lectures.length === 0 ? (
          <Empty>该筛选条件下暂无讲义</Empty>
        ) : (
          <table>
            <thead>
              <tr>
                <th>标题</th>
                <th>学科</th>
                <th>上传者</th>
                <th>上传时间</th>
                <th>知识块</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {lectures.map((l) => (
                <tr key={l.id}>
                  <td>
                    <b>{l.title}</b>
                    {openId === l.id ? (
                      <div className="col small" style={{ marginTop: 8, gap: 8 }}>
                        {chunks === null ? (
                          <span className="muted">加载知识块…</span>
                        ) : (
                          chunks.map((c) => (
                            <div key={c.id} className="card" style={{ padding: 10 }}>
                              <div className="row small muted">
                                <span className="tag">{c.location}</span>
                                {c.keywords.map((k) => (
                                  <span key={k} className="tag">
                                    {k}
                                  </span>
                                ))}
                              </div>
                              <div style={{ marginTop: 6 }}>{c.text}</div>
                            </div>
                          ))
                        )}
                      </div>
                    ) : null}
                  </td>
                  <td>
                    <span className="tag brand">{l.subject}</span>
                  </td>
                  <td className="muted">{l.uploader}</td>
                  <td className="muted small">{new Date(l.uploaded_at).toLocaleString("zh-CN")}</td>
                  <td>{l.chunk_count}</td>
                  <td>
                    <div className="row" style={{ gap: 6, flexWrap: "nowrap" }}>
                      <button className="sm" onClick={() => openChunks(l.id)}>
                        {openId === l.id ? "收起" : "知识块"}
                      </button>
                      <button className="sm danger" onClick={() => remove(l.id)}>
                        删除
                      </button>
                    </div>
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

function UploadCard({
  subjects,
  busy,
  onUpload,
}: {
  subjects: string[];
  busy: boolean;
  onUpload: (form: FormData) => Promise<boolean>;
}) {
  const [title, setTitle] = useState("");
  const [subject, setSubject] = useState(subjects[0] ?? "");
  const [file, setFile] = useState<File | null>(null);

  useEffect(() => {
    if (!subject && subjects.length) setSubject(subjects[0]);
  }, [subjects, subject]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!file || !title || !subject) return;
    const form = new FormData();
    form.set("subject", subject);
    form.set("title", title);
    form.set("file", file);
    if (await onUpload(form)) {
      setTitle("");
      setFile(null);
      (e.target as HTMLFormElement).reset();
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <h3>上传讲义</h3>
      <div className="grid cols-3">
        <label className="field">
          <span>标题</span>
          <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="如：函数的单调性" />
        </label>
        <label className="field">
          <span>学科</span>
          <select value={subject} onChange={(e) => setSubject(e.target.value)}>
            {subjects.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>文件（.txt / .md / .markdown）</span>
          <input type="file" accept=".txt,.md,.markdown" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        </label>
      </div>
      <button className="primary" disabled={busy || !file || !title || !subject}>
        {busy ? "上传中…" : "上传并切块"}
      </button>
    </form>
  );
}
