"use client";

/**
 * 学科助手对话。发送走 SSE：执行过程逐步点亮 → 文本逐字流出 → 结束事件带来源引用。
 */

import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";

import { apiGet, apiPost } from "@/lib/api";
import type { Res } from "@/lib/api";
import { streamMessage, type DoneEvent, type TraceEvent } from "@/lib/sse";
import { errorMessage } from "@/lib/session";
import { Empty, ErrorBanner, Loading, PageHead } from "@/components/ui";

type Assistant = Res<"/api/assistants">[number];
type Message = Res<"/api/conversations/{conversation_id}/messages">[number];
type Source = Message["sources"][number];

export default function ChatPage() {
  return (
    <Suspense fallback={<Loading />}>
      <ChatView />
    </Suspense>
  );
}

function ChatView() {
  const params = useSearchParams();
  const subjectParam = params.get("subject");

  const [assistants, setAssistants] = useState<Assistant[] | null>(null);
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [error, setError] = useState<string | null>(null);

  // 流式中的临时状态
  const [pendingTrace, setPendingTrace] = useState<TraceEvent[]>([]);
  const [pendingText, setPendingText] = useState("");
  const [pendingSources, setPendingSources] = useState<Source[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [draft, setDraft] = useState("");
  const abortRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    apiGet("/api/assistants")
      .then((rows) => {
        setAssistants(rows);
        const match = subjectParam ? rows.find((a) => a.subject === subjectParam) : undefined;
        setCurrentId((prev) => prev ?? match?.id ?? rows[0]?.id ?? null);
      })
      .catch((e) => setError(errorMessage(e)));
  }, [subjectParam]);

  // 切换助手：幂等获取会话并载入历史
  useEffect(() => {
    if (!currentId) return;
    abortRef.current?.abort();
    setStreaming(false);
    setPendingTrace([]);
    setPendingText("");
    setPendingSources([]);
    setMessages([]);
    setConversationId(null);

    apiPost("/api/conversations", { assistant_id: currentId })
      .then((c) => {
        setConversationId(c.id);
        setMessages(c.messages);
      })
      .catch((e) => setError(errorMessage(e)));
  }, [currentId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, pendingText, pendingTrace]);

  const reloadHistory = useCallback(async (id: string) => {
    const rows = await apiGet("/api/conversations/{conversation_id}/messages", {
      path: { conversation_id: id },
    });
    setMessages(rows);
  }, []);

  async function send() {
    const content = draft.trim();
    if (!content || !conversationId || streaming) return;

    setDraft("");
    setError(null);
    setStreaming(true);
    setPendingTrace([]);
    setPendingText("");
    setPendingSources([]);

    // 乐观插入用户消息，后端也会持久化同一条
    setMessages((prev) => [
      ...prev,
      {
        id: `local-${Date.now()}`,
        conversation_id: conversationId,
        role: "user",
        content,
        skill_key: null,
        sources: [],
        trace: [],
        created_at: new Date().toISOString(),
      },
    ]);

    const controller = new AbortController();
    abortRef.current = controller;

    let done: DoneEvent | null = null;
    try {
      await streamMessage(
        conversationId,
        content,
        {
          onTrace: (step) => setPendingTrace((prev) => [...prev, step]),
          onDelta: (d) => setPendingText((prev) => prev + d.text),
          onDone: (d) => {
            done = d;
            setPendingSources(d.sources);
          },
          onError: (e) => setError(e.detail),
        },
        controller.signal,
      );
      if (done) await reloadHistory(conversationId);
    } catch (e) {
      if (!controller.signal.aborted) setError(errorMessage(e));
    } finally {
      setStreaming(false);
      setPendingTrace([]);
      setPendingText("");
      setPendingSources([]);
      abortRef.current = null;
    }
  }

  const current = assistants?.find((a) => a.id === currentId) ?? null;

  if (assistants === null) return <Loading />;
  if (assistants.length === 0) return <Empty>本班尚未开设学科助手</Empty>;

  return (
    <>
      <PageHead
        title="学科助手"
        desc="回答基于本班知识库，并标注来源；检索不到相关资料时不会臆测。"
      />

      <div className="row" style={{ marginBottom: 12 }}>
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

      <ErrorBanner error={error} />

      <div className="card chat">
        <div className="stream">
          {messages.length === 0 && !streaming ? (
            <Empty>
              向{current?.name ?? "助手"}提问吧。启用「解题引导」时，题目类提问会得到思路引导而非直接答案。
            </Empty>
          ) : null}

          {messages.map((m) =>
            m.role === "user" ? (
              <div key={m.id} className="bubble user">
                {m.content}
              </div>
            ) : (
              <div key={m.id} className="bubble assistant">
                {m.trace.length ? <TraceList steps={m.trace} /> : null}
                {m.skill_key ? (
                  <div style={{ marginBottom: 6 }}>
                    <span className="tag brand">技能 {skillName(current, m.skill_key)}</span>
                  </div>
                ) : null}
                {m.content}
                <SourceList sources={m.sources} />
              </div>
            ),
          )}

          {streaming ? (
            <div className="bubble assistant">
              {pendingTrace.length ? <TraceList steps={pendingTrace} live /> : null}
              {pendingText || <span className="muted">正在思考…</span>}
              <SourceList sources={pendingSources} />
            </div>
          ) : null}

          <div ref={bottomRef} />
        </div>

        <div className="composer">
          <textarea
            value={draft}
            placeholder="输入你的问题，Enter 发送，Shift+Enter 换行"
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
          />
          <button className="primary" disabled={streaming || !draft.trim()} onClick={send}>
            {streaming ? "回答中…" : "发送"}
          </button>
        </div>
      </div>
    </>
  );
}

/** 消息只带技能 key，展示时换成助手配置里的技能名。 */
function skillName(assistant: Assistant | null, key: string): string {
  return assistant?.skills.find((s) => s.key === key)?.name ?? key;
}

function TraceList({ steps, live }: { steps: TraceEvent[]; live?: boolean }) {
  return (
    <div className="trace">
      <div className="small muted" style={{ marginBottom: 4 }}>
        执行过程{live ? "（进行中）" : ""}
      </div>
      {steps.map((s, i) => (
        <div key={i} className="step">
          <span>{s.icon}</span>
          <span>
            <b>{s.label}</b>
            {s.detail ? ` —— ${s.detail}` : ""}
          </span>
        </div>
      ))}
    </div>
  );
}

function SourceList({ sources }: { sources: Source[] }) {
  if (!sources.length) return null;
  return (
    <div className="sources">
      <div className="muted" style={{ marginBottom: 4 }}>
        来源引用
      </div>
      {sources.map((s, i) => (
        <div key={i}>
          <span className="tag">{s.lecture_title}</span> <span className="muted">{s.location}</span>
        </div>
      ))}
    </div>
  );
}
