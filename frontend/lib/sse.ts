/**
 * 助手对话的 SSE 消费（design.md D5）。
 *
 * 发送消息走 POST，原生 EventSource 用不了，因此用 fetch + ReadableStream
 * 手动解析事件流。事件载荷类型同样来自生成的契约，不手写。
 */

import type { components } from "@/types/api";
import { API_BASE, ApiError, authHeaders } from "@/lib/api";

type Schemas = components["schemas"];

export type TraceEvent = Schemas["ChatTraceEvent"];
export type DeltaEvent = Schemas["ChatDeltaEvent"];
export type DoneEvent = Schemas["ChatDoneEvent"];
export type ErrorEvent = Schemas["ChatErrorEvent"];

export interface ChatHandlers {
  onTrace?: (step: TraceEvent) => void;
  onDelta?: (delta: DeltaEvent) => void;
  onDone?: (done: DoneEvent) => void;
  onError?: (err: ErrorEvent) => void;
}

/** 把 `event: x\ndata: {...}` 的一个块分派给对应回调。 */
function dispatch(block: string, handlers: ChatHandlers) {
  let name = "message";
  const dataLines: string[] = [];
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) name = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
  }
  if (!dataLines.length) return;
  const payload: unknown = JSON.parse(dataLines.join("\n"));
  switch (name) {
    case "trace":
      handlers.onTrace?.(payload as TraceEvent);
      break;
    case "delta":
      handlers.onDelta?.(payload as DeltaEvent);
      break;
    case "done":
      handlers.onDone?.(payload as DoneEvent);
      break;
    case "error":
      handlers.onError?.(payload as ErrorEvent);
      break;
  }
}

export async function streamMessage(
  conversationId: string,
  content: string,
  handlers: ChatHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const headers = authHeaders({ "Content-Type": "application/json" });
  const res = await fetch(
    `${API_BASE}/api/conversations/${encodeURIComponent(conversationId)}/messages`,
    { method: "POST", headers, body: JSON.stringify({ content }), signal },
  );

  if (!res.ok || !res.body) {
    const text = await res.text().catch(() => "");
    throw new ApiError(res.status, text || `对话请求失败（${res.status}）`);
  }

  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += value;
      // SSE 以空行分隔事件块
      let sep = buffer.indexOf("\n\n");
      while (sep >= 0) {
        dispatch(buffer.slice(0, sep), handlers);
        buffer = buffer.slice(sep + 2);
        sep = buffer.indexOf("\n\n");
      }
    }
    if (buffer.trim()) dispatch(buffer, handlers);
  } finally {
    reader.cancel().catch(() => undefined);
  }
}
