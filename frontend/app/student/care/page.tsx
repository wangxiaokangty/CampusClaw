"use client";

/**
 * 心情树洞：情绪识别与共情回应，仅本人可读。
 * 不做心理诊断；出现高风险表达时附加固定的求助引导文案。
 */

import { useEffect, useRef, useState } from "react";

import { apiGet, apiPost } from "@/lib/api";
import type { Res } from "@/lib/api";
import { errorMessage } from "@/lib/session";
import { Empty, ErrorBanner, Loading, PageHead } from "@/components/ui";

type CareMessage = Res<"/api/care/messages">[number];

export default function StudentCarePage() {
  const [messages, setMessages] = useState<CareMessage[] | null>(null);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [escalated, setEscalated] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    apiGet("/api/care/messages").then(setMessages).catch((e) => setError(errorMessage(e)));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send() {
    const content = draft.trim();
    if (!content || busy) return;
    setBusy(true);
    setError(null);
    setDraft("");
    try {
      const reply = await apiPost("/api/care/messages", { content });
      setEscalated(reply.escalated);
      setMessages(await apiGet("/api/care/messages"));
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHead
        title="心情树洞"
        desc="只有你能看到这里的内容，不会进入教师端的任何统计，也不用于评价。"
      />
      <ErrorBanner error={error} />

      {escalated ? (
        <div className="notice" style={{ marginBottom: 12 }}>
          回应中附上了求助引导——请认真看一看，你不需要一个人扛。
        </div>
      ) : null}

      <div className="card chat">
        <div className="stream">
          {messages === null ? (
            <Loading />
          ) : messages.length === 0 ? (
            <Empty>今天过得怎么样？随便说点什么都可以。</Empty>
          ) : (
            messages.map((m) => (
              <div key={m.id} className={`bubble ${m.role === "user" ? "user" : "assistant"}`}>
                {m.role === "user" && m.emotion ? (
                  <div style={{ marginBottom: 4 }}>
                    <span className="tag">{m.emotion}</span>
                  </div>
                ) : null}
                {m.content}
              </div>
            ))
          )}
          <div ref={bottomRef} />
        </div>

        <div className="composer">
          <textarea
            value={draft}
            placeholder="说说你的感受，Enter 发送"
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
          />
          <button className="primary" disabled={busy || !draft.trim()} onClick={send}>
            {busy ? "发送中…" : "发送"}
          </button>
        </div>
      </div>
    </>
  );
}
