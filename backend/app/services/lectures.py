"""讲义解析与切块。"""

import re
import uuid

SUPPORTED_SUFFIXES = {".txt", ".md", ".markdown"}

# 形如「第 2 页」「3.1 节」「例题 1」的位置标记
LOCATION_PATTERN = re.compile(
    r"^\s*(第\s*[0-9一二三四五六七八九十]+\s*[页章节]|[0-9]+(\.[0-9]+)*\s*节|例题\s*[0-9]+|#{1,6}\s+.+)\s*$"
)

STOPWORDS = {"的", "了", "是", "在", "和", "与", "对于", "可以", "我们", "这个", "如果"}


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def extract_keywords(text: str, limit: int = 6) -> list[str]:
    """从正文提取检索关键词：中文双字词 + 字母数字串，按出现频次取前若干。"""
    tokens = re.findall(r"[一-龥]{2,6}", text) + re.findall(r"[a-zA-Z]{2,}", text)
    freq: dict[str, int] = {}
    for token in tokens:
        if token in STOPWORDS:
            continue
        freq[token] = freq.get(token, 0) + 1
    ordered = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
    return [word for word, _ in ordered[:limit]]


def split_into_chunks(content: str, title: str) -> list[tuple[str, str]]:
    """把讲义正文切成 [(位置标识, 正文)]。

    优先按显式的位置标记（第 N 页 / N.N 节 / 例题 N / Markdown 标题）分段；
    没有标记时按空行分段，位置退化为「第 N 段」。
    """
    lines = content.replace("\r\n", "\n").split("\n")
    sections: list[tuple[str, list[str]]] = []
    current_label: str | None = None
    current_body: list[str] = []

    for line in lines:
        if LOCATION_PATTERN.match(line) and line.strip():
            if current_body and any(x.strip() for x in current_body):
                sections.append((current_label or f"第 {len(sections) + 1} 段", current_body))
            current_label = line.strip().lstrip("#").strip()
            current_body = []
        else:
            current_body.append(line)
    if current_body and any(x.strip() for x in current_body):
        sections.append((current_label or f"第 {len(sections) + 1} 段", current_body))

    chunks = [
        (label, "\n".join(body).strip())
        for label, body in sections
        if "\n".join(body).strip()
    ]

    if not chunks:
        # 无位置标记：按空行分段
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", content) if p.strip()]
        chunks = [(f"第 {i + 1} 段", p) for i, p in enumerate(paragraphs)]

    if not chunks and content.strip():
        chunks = [("全文", content.strip())]

    return chunks
