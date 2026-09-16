"""SSE 响应解析辅助。"""

import json


def parse_sse(text: str) -> list[tuple[str, dict]]:
    """把 text/event-stream 响应体解析为 [(event, data)]。"""
    events: list[tuple[str, dict]] = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        name, payload = None, None
        for line in block.split("\n"):
            if line.startswith("event: "):
                name = line[len("event: ") :]
            elif line.startswith("data: "):
                payload = json.loads(line[len("data: ") :])
        if name is not None:
            events.append((name, payload or {}))
    return events


def kinds(events) -> list[str]:
    return [name for name, _ in events]


def collect_text(events) -> str:
    return "".join(d["text"] for n, d in events if n == "delta")


def done_of(events) -> dict:
    return next(d for n, d in events if n == "done")
