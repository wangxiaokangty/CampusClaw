"use client";

/** 助手配置：提示词、绑定讲义、技能增删改与启停、技能包导入、MCP 服务器。教师可写，学生只读。 */

import { useCallback, useEffect, useState } from "react";

import { apiDelete, apiGet, apiPatch, apiPost, apiUpload } from "@/lib/api";
import type { Res } from "@/lib/api";
import { errorMessage } from "@/lib/session";
import { Empty, ErrorBanner, Loading, PageHead } from "@/components/ui";

type Assistant = Res<"/api/assistants">[number];
type Skill = Assistant["skills"][number];
type Lecture = Res<"/api/lectures">[number];

export default function TeacherAssistantsPage() {
  const [assistants, setAssistants] = useState<Assistant[] | null>(null);
  const [lectures, setLectures] = useState<Lecture[]>([]);
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [as, ls] = await Promise.all([apiGet("/api/assistants"), apiGet("/api/lectures")]);
      setAssistants(as);
      setLectures(ls);
      setCurrentId((prev) => prev ?? as[0]?.id ?? null);
    } catch (e) {
      setError(errorMessage(e));
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const current = assistants?.find((a) => a.id === currentId) ?? null;

  return (
    <>
      <PageHead title="助手配置" desc="修改提示词、技能与外部工具。学生只读，无法改变助手行为规则。" />
      <ErrorBanner error={error} />

      {assistants === null ? (
        <Loading />
      ) : assistants.length === 0 ? (
        <Empty>本班尚未开设学科助手</Empty>
      ) : (
        <>
          <div className="row" style={{ marginBottom: 14 }}>
            {assistants.map((a) => (
              <button
                key={a.id}
                className={a.id === currentId ? "primary" : ""}
                onClick={() => setCurrentId(a.id)}
              >
                {a.icon} {a.subject}
              </button>
            ))}
          </div>

          {current ? (
            <AssistantPanel
              assistant={current}
              lectures={lectures}
              onChanged={load}
              onError={setError}
            />
          ) : null}
        </>
      )}
    </>
  );
}

function AssistantPanel({
  assistant,
  lectures,
  onChanged,
  onError,
}: {
  assistant: Assistant;
  lectures: Lecture[];
  onChanged: () => void;
  onError: (msg: string | null) => void;
}) {
  const [prompt, setPrompt] = useState(assistant.prompt);
  const [bound, setBound] = useState<string[]>(assistant.bound_lecture_ids);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setPrompt(assistant.prompt);
    setBound(assistant.bound_lecture_ids);
  }, [assistant]);

  const sameSubject = lectures.filter((l) => l.subject === assistant.subject);
  const otherSubject = lectures.filter((l) => l.subject !== assistant.subject);

  async function save() {
    setSaving(true);
    onError(null);
    try {
      await apiPatch(
        "/api/assistants/{assistant_id}",
        { prompt, bound_lecture_ids: bound },
        { path: { assistant_id: assistant.id } },
      );
      onChanged();
    } catch (e) {
      onError(errorMessage(e));
    } finally {
      setSaving(false);
    }
  }

  function toggleBound(id: string) {
    setBound((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  const dirty =
    prompt !== assistant.prompt ||
    bound.join("|") !== assistant.bound_lecture_ids.join("|");

  return (
    <div className="col" style={{ gap: 14 }}>
      <div className="card">
        <h3>
          {assistant.icon} {assistant.name}
        </h3>
        <div className="row small muted" style={{ marginBottom: 10 }}>
          <span className="tag">学科 {assistant.subject}</span>
          <span className="tag mono" title="明文不出现在任何响应中">
            API Key {assistant.api_key_masked || "未配置"}
          </span>
        </div>

        <label className="field">
          <span>系统提示词</span>
          <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={4} />
        </label>

        <label className="field">
          <span>绑定讲义（检索范围，仅限同学科）</span>
        </label>
        {sameSubject.length === 0 ? (
          <p className="muted small">该学科暂无讲义</p>
        ) : (
          <div className="row">
            {sameSubject.map((l) => (
              <button
                key={l.id}
                className={`sm${bound.includes(l.id) ? " primary" : ""}`}
                onClick={() => toggleBound(l.id)}
              >
                {bound.includes(l.id) ? "✓ " : ""}
                {l.title}
              </button>
            ))}
          </div>
        )}
        {otherSubject.length ? (
          <p className="small muted" style={{ marginBottom: 0 }}>
            其他学科的 {otherSubject.length} 份讲义不可绑定——跨学科绑定会被后端拒绝。
          </p>
        ) : null}

        <div className="row" style={{ marginTop: 12 }}>
          <button className="primary" disabled={!dirty || saving} onClick={save}>
            {saving ? "保存中…" : "保存配置"}
          </button>
          {dirty ? <span className="small muted">有未保存的修改</span> : null}
        </div>
      </div>

      <SkillsCard assistant={assistant} onChanged={onChanged} onError={onError} />
      <McpCard assistant={assistant} onChanged={onChanged} onError={onError} />
    </div>
  );
}

function SkillsCard({
  assistant,
  onChanged,
  onError,
}: {
  assistant: Assistant;
  onChanged: () => void;
  onError: (msg: string | null) => void;
}) {
  const availableTools = assistant.mcp_servers.flatMap((s) => s.tools);
  const [draft, setDraft] = useState({ name: "", when: "", behavior: "", tools: [] as string[] });
  const [importing, setImporting] = useState<string | null>(null);

  async function act(fn: () => Promise<unknown>) {
    onError(null);
    try {
      await fn();
      onChanged();
    } catch (e) {
      onError(errorMessage(e));
    }
  }

  const toggle = (s: Skill) =>
    act(() =>
      apiPatch(
        "/api/assistants/{assistant_id}/skills/{skill_id}",
        { enabled: !s.enabled },
        { path: { assistant_id: assistant.id, skill_id: s.id } },
      ),
    );

  const remove = (s: Skill) =>
    act(() =>
      apiDelete("/api/assistants/{assistant_id}/skills/{skill_id}", {
        path: { assistant_id: assistant.id, skill_id: s.id },
      }),
    );

  async function create() {
    if (!draft.name) return;
    await act(async () => {
      await apiPost("/api/assistants/{assistant_id}/skills", { ...draft, enabled: true }, {
        path: { assistant_id: assistant.id },
      });
      setDraft({ name: "", when: "", behavior: "", tools: [] });
    });
  }

  async function importPack(file: File) {
    onError(null);
    setImporting(null);
    const form = new FormData();
    form.set("file", file);
    try {
      const preview = await apiUpload("/api/assistants/{assistant_id}/skills/import", form, {
        path: { assistant_id: assistant.id },
      });
      setDraft({
        name: preview.name,
        when: preview.when,
        behavior: preview.behavior,
        tools: preview.tools.filter((t) => availableTools.includes(t)),
      });
      setImporting(
        preview.manifest_found
          ? `已从清单解析出「${preview.name}」，确认后新增。`
          : preview.note || "未找到清单，需手动补全后再新增。",
      );
    } catch (e) {
      onError(errorMessage(e));
    }
  }

  return (
    <div className="card">
      <h3>AI 技能</h3>
      <table>
        <thead>
          <tr>
            <th>技能</th>
            <th>触发时机</th>
            <th>行为</th>
            <th>工具</th>
            <th>状态</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {assistant.skills.map((s) => (
            <tr key={s.id}>
              <td>
                <b>{s.name}</b>
                {s.required ? <div className="tag">内置必需</div> : null}
              </td>
              <td className="muted small">{s.when}</td>
              <td className="muted small">{s.behavior}</td>
              <td>
                <div className="row" style={{ gap: 4 }}>
                  {s.tools.map((t) => (
                    <span key={t} className="tag mono small">
                      {t}
                    </span>
                  ))}
                </div>
              </td>
              <td>
                <span className={`tag ${s.enabled ? "ok" : ""}`}>{s.enabled ? "已启用" : "已停用"}</span>
              </td>
              <td>
                <div className="row" style={{ gap: 6, flexWrap: "nowrap" }}>
                  <button className="sm" onClick={() => toggle(s)}>
                    {s.enabled ? "停用" : "启用"}
                  </button>
                  {s.required ? null : (
                    <button className="sm danger" onClick={() => remove(s)}>
                      删除
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div style={{ marginTop: 16, paddingTop: 14, borderTop: "1px solid var(--border)" }}>
        <h3>新增自定义技能</h3>
        {importing ? <div className="notice" style={{ marginBottom: 10 }}>{importing}</div> : null}
        <div className="grid cols-2">
          <label className="field">
            <span>名称</span>
            <input value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} />
          </label>
          <label className="field">
            <span>触发时机</span>
            <input value={draft.when} onChange={(e) => setDraft({ ...draft, when: e.target.value })} />
          </label>
        </div>
        <label className="field">
          <span>行为描述</span>
          <input
            value={draft.behavior}
            onChange={(e) => setDraft({ ...draft, behavior: e.target.value })}
          />
        </label>
        <label className="field">
          <span>绑定工具（仅限已连接服务器暴露的工具）</span>
        </label>
        <div className="row">
          {availableTools.map((t) => (
            <button
              key={t}
              className={`sm mono${draft.tools.includes(t) ? " primary" : ""}`}
              onClick={() =>
                setDraft({
                  ...draft,
                  tools: draft.tools.includes(t)
                    ? draft.tools.filter((x) => x !== t)
                    : [...draft.tools, t],
                })
              }
            >
              {t}
            </button>
          ))}
        </div>
        <div className="row" style={{ marginTop: 12 }}>
          <button className="primary" disabled={!draft.name} onClick={create}>
            新增技能
          </button>
          <label className="btn" style={{ cursor: "pointer" }}>
            从 .zip 技能包导入
            <input
              type="file"
              accept=".zip"
              hidden
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) importPack(f);
                e.target.value = "";
              }}
            />
          </label>
        </div>
      </div>
    </div>
  );
}

function McpCard({
  assistant,
  onChanged,
  onError,
}: {
  assistant: Assistant;
  onChanged: () => void;
  onError: (msg: string | null) => void;
}) {
  const [draft, setDraft] = useState({ name: "", url: "" });

  async function act(fn: () => Promise<unknown>) {
    onError(null);
    try {
      await fn();
      onChanged();
    } catch (e) {
      onError(errorMessage(e));
    }
  }

  return (
    <div className="card">
      <h3>MCP 服务器</h3>
      <p className="small muted" style={{ marginTop: 0 }}>
        本阶段握手为模拟行为，不发起真实 MCP 协议通信。
      </p>
      <table>
        <thead>
          <tr>
            <th>名称</th>
            <th>地址</th>
            <th>状态</th>
            <th>工具</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {assistant.mcp_servers.map((s) => (
            <tr key={s.id}>
              <td>
                <b>{s.name}</b>
                {s.builtin ? <div className="tag">内置</div> : null}
              </td>
              <td className="mono small muted">{s.url}</td>
              <td>
                <span className={`tag ${s.status === "connected" ? "ok" : "danger"}`}>
                  {s.status === "connected" ? "已连接" : "未连接"}
                </span>
              </td>
              <td>
                <div className="row" style={{ gap: 4 }}>
                  {s.tools.map((t) => (
                    <span key={t} className="tag mono small">
                      {t}
                    </span>
                  ))}
                </div>
              </td>
              <td>
                {s.builtin ? null : (
                  <button
                    className="sm danger"
                    onClick={() =>
                      act(() =>
                        apiDelete("/api/assistants/{assistant_id}/mcp-servers/{server_id}", {
                          path: { assistant_id: assistant.id, server_id: s.id },
                        }),
                      )
                    }
                  >
                    断开
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="grid cols-2" style={{ marginTop: 14 }}>
        <label className="field">
          <span>名称</span>
          <input value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} />
        </label>
        <label className="field">
          <span>地址</span>
          <input
            className="mono"
            placeholder="mcp://tools/example"
            value={draft.url}
            onChange={(e) => setDraft({ ...draft, url: e.target.value })}
          />
        </label>
      </div>
      <button
        className="primary"
        disabled={!draft.name || !draft.url}
        onClick={() =>
          act(async () => {
            await apiPost("/api/assistants/{assistant_id}/mcp-servers", draft, {
              path: { assistant_id: assistant.id },
            });
            setDraft({ name: "", url: "" });
          })
        }
      >
        连接并发现工具
      </button>
    </div>
  );
}
