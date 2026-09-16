"""AI 能力的 mock 实现。

行为对齐 CampusClaw 前端演示中的规则逻辑：关键词检索 → 技能路由 →
模板拼装。它**不伪装成真实模型**——命名、文档与接口标注都表明这是演示实现。

真实 LLM 接入时整体替换本模块即可，base.py 中的签名保持不变。
"""

import asyncio
import re
from collections.abc import AsyncIterator

from app.ai.base import (
    AssistantContext,
    CareResult,
    Chunk,
    ChatEvent,
    DeltaEvent,
    DoneEvent,
    ExplainResult,
    GradeResult,
    ProfileInput,
    ProfileResult,
    Retrieved,
    SourceRef,
    TraceEvent,
    TraceStep,
)

SKILL_LABELS = {
    "guide": "解题引导",
    "grade": "作业批改",
    "mistake": "错题讲解",
    "care": "关怀式对话",
}

# 单字也具检索意义的常用字
SIGNIFICANT_SINGLE_CHARS = {"根", "解", "集", "导", "幂"}

QUESTION_MARKERS = (
    "?", "？", "怎么", "如何", "为什么", "求", "解", "证明", "判断", "是多少", "等于",
)

TOOL_TRIGGER = re.compile(
    r"[=xX²√\d]|方程|函数|求解|计算|翻译|译|语法|时态|语态|配平|摩尔|物质的量|"
    r"受力|公式|单位|史料|年代|朝代"
)


def tokenize(query: str) -> list[str]:
    """提取检索词：中文双字以上词、字母数字串，以及若干有意义的单字。"""
    words = re.findall(r"[一-龥]{2,}", query)
    alnum = re.findall(r"[a-zA-Z0-9]+", query)
    singles = [
        c for c in re.findall(r"[一-龥]", query)
        if c in SIGNIFICANT_SINGLE_CHARS
    ]
    seen: dict[str, None] = {}
    for token in (*words, *alnum, *singles):
        seen.setdefault(token, None)
    return list(seen)


def _is_question(text: str) -> bool:
    return any(marker in text for marker in QUESTION_MARKERS)


def _estimate_tokens(text: str) -> int:
    return max(20, round(len(text) * 1.6))


def _sources_of(hits: list[Retrieved], limit: int = 2) -> tuple[SourceRef, ...]:
    return tuple(
        SourceRef(
            lecture_title=h.chunk.lecture_title,
            location=h.chunk.location,
            text=h.chunk.text,
        )
        for h in hits[:limit]
    )


class MockProvider:
    """演示用的规则实现。所有输出对相同输入确定性一致。"""

    name = "mock"

    # --- 检索 ---------------------------------------------------------------

    def retrieve(self, chunks: list[Chunk], query: str) -> list[Retrieved]:
        tokens = tokenize(query.strip())
        if not tokens:
            return []
        hits: list[Retrieved] = []
        for chunk in chunks:
            score = 0
            for token in tokens:
                if any(token in k or k in token for k in chunk.keywords):
                    score += 3
                if token in chunk.text:
                    score += 2
                if token in chunk.lecture_title:
                    score += 1
            if score > 0:
                hits.append(Retrieved(chunk=chunk, score=float(score)))
        hits.sort(key=lambda h: (-h.score, h.chunk.id))
        return hits

    # --- 对话 ---------------------------------------------------------------

    def _pick_tool(self, assistant: AssistantContext, question: str) -> str | None:
        if not assistant.tools or not TOOL_TRIGGER.search(question):
            return None
        binding = assistant.tools[0]
        return f"{binding.tool}@{binding.server_name}"

    def _build_trace(
        self,
        skill_key: str | None,
        action: str,
        hit_count: int,
        sources: tuple[SourceRef, ...],
        tool: str | None,
    ) -> list[TraceStep]:
        label = SKILL_LABELS.get(skill_key or "", skill_key) or "直接问答"
        matched = (
            "，".join(f"{s.lecture_title}·{s.location}" for s in sources)
            if sources
            else "无匹配"
        )
        steps = [
            TraceStep("🧠", "理解问题意图", "解析提问并规划步骤"),
            TraceStep("🔎", "检索班级知识库", f"命中 {hit_count} 条片段（{matched}）"),
            TraceStep("🧩", f"路由到技能：{label}", action),
        ]
        if tool:
            tool_name, server_name = tool.split("@", 1)
            steps.append(
                TraceStep("🔌", f"调用 MCP 工具：{tool_name}", f"来自服务器 {server_name}")
            )
        steps.append(TraceStep("✍️", "组织并生成回答", "流式输出中"))
        return steps

    def plan_answer(
        self, assistant: AssistantContext, question: str, chunks: list[Chunk]
    ) -> tuple[str | None, str, tuple[SourceRef, ...], list[TraceStep], str]:
        """返回 (skill_key, action, sources, trace, text)。对话与测试共用。"""
        hits = self.retrieve(chunks, question)
        sources = _sources_of(hits)
        top = hits[0].chunk if hits else None

        # 无命中：明确拒绝臆测，不给出实质性结论
        if top is None:
            skill_key = "guide" if assistant.guide_enabled else None
            action = (
                "解题引导（无命中）" if assistant.guide_enabled else "直接问答（无命中）"
            )
            text = (
                "在本班知识库中没有检索到与该问题直接相关的资料，因此我不能凭空给出结论。"
                "建议你补充题目条件，或让老师上传相关讲义后再试。"
            )
            trace = self._build_trace(skill_key, action, 0, (), None)
            return skill_key, action, (), trace, text

        tool = self._pick_tool(assistant, question)
        tool_note = (
            f"\n（已通过 MCP 工具 {tool.split('@')[0]} 辅助验证关键步骤）" if tool else ""
        )

        # 解题引导：引导思路，不直接给最终答案
        if assistant.guide_enabled and _is_question(question):
            action = "解题引导"
            text = (
                "\n".join(
                    [
                        "我们一起理清思路（这里先不直接给最终答案）：",
                        f"1. 回顾相关知识：{top.text}",
                        "2. 想一想：题目给了哪些条件？可以先判断关键量（如判别式、单调区间）吗？",
                        "3. 试着写出第一步推导，把结果发给我，我来帮你检查方向是否正确。",
                    ]
                )
                + tool_note
            )
            trace = self._build_trace("guide", action, len(hits), sources, tool)
            return "guide", action, sources, trace, text

        # 直接讲解
        action = "直接问答"
        extra = (
            f"补充：{hits[1].chunk.text}"
            if len(hits) > 1
            else "如果需要，我可以给出完整的解题步骤。"
        )
        text = "\n".join(["直接为你讲解：", top.text, extra]) + tool_note
        trace = self._build_trace(None, action, len(hits), sources, tool)
        return None, action, sources, trace, text

    async def answer(
        self,
        assistant: AssistantContext,
        question: str,
        chunks: list[Chunk],
        *,
        trace_interval: float = 0.25,
        delta_interval: float = 0.02,
        delta_size: int = 6,
    ) -> AsyncIterator[ChatEvent]:
        """真实的流式推送。mock 的只是内容，不是传输方式。"""
        skill_key, action, sources, trace, text = self.plan_answer(
            assistant, question, chunks
        )

        elapsed_ms = 0
        for step in trace:
            await asyncio.sleep(trace_interval)
            elapsed_ms += int(trace_interval * 1000)
            yield TraceEvent(step=step)

        for start in range(0, len(text), delta_size):
            await asyncio.sleep(delta_interval)
            elapsed_ms += int(delta_interval * 1000)
            yield DeltaEvent(text=text[start : start + delta_size])

        yield DoneEvent(
            skill_key=skill_key,
            action=action,
            sources=sources,
            full_text=text,
            tokens=_estimate_tokens(text),
            cost_ms=elapsed_ms,
        )

    # --- 批改 ---------------------------------------------------------------

    def grade(
        self, homework_title: str, content: str, chunks: list[Chunk]
    ) -> GradeResult:
        answer = content.strip()
        tokens = 280 + round(len(answer) * 1.2)

        if len(answer) < 4:
            return GradeResult(
                score=20,
                comment="作答过于简略，未给出必要的推导过程。",
                basis="依据本班知识库要点评估。",
                wrong=True,
                tokens=tokens,
            )

        if "一元二次方程" in homework_title:
            signals = [
                bool(re.search(r"因式分解|十字相乘|\(x", answer)),
                bool(re.search(r"求根公式|判别式|Δ|b²", answer)),
                bool(re.search(r"x\s*=\s*2|x\s*=\s*3|=2|=3", answer)),
            ]
            hit = sum(signals)
            return GradeResult(
                score=min(99, 60 + hit * 13),
                comment=(
                    "方法与结论基本正确，过程清晰。"
                    if hit >= 2
                    else "方向可行，但过程不完整，建议补充判别式或求根公式验证。"
                ),
                basis="依据《一元二次方程与求根公式》第 2、3 页与例题 1。",
                wrong=hit < 2,
                tokens=tokens,
            )

        if "单调性" in homework_title:
            ok = bool(re.search(r"增函数|递增", answer)) and "减函数" not in answer
            return GradeResult(
                score=90 if ok else 60,
                comment=(
                    "判断正确：对称轴 x=2 右侧为增函数，理由充分。"
                    if ok
                    else "结论有误：二次函数在对称轴右侧应为增函数，需用作差法或导数验证。"
                ),
                basis="依据《函数的单调性》3.1、3.2 节。",
                wrong=not ok,
                tokens=tokens,
            )

        if "集合" in homework_title:
            ok = bool(re.search(r"∩|∪|交集|并集", answer))
            return GradeResult(
                score=88 if ok else 55,
                comment=(
                    "集合运算表述正确。" if ok else "需明确写出交集与并集的具体元素。"
                ),
                basis="依据《集合与常用逻辑用语》第 1 页。",
                wrong=not ok,
                tokens=tokens,
            )

        hits = self.retrieve(chunks, f"{homework_title} {answer}")
        basis = (
            f"依据《{hits[0].chunk.lecture_title}》{hits[0].chunk.location}。"
            if hits
            else "依据本班知识库。"
        )
        return GradeResult(
            score=75,
            comment="作答基本合理，可进一步补充依据。",
            basis=basis,
            wrong=False,
            tokens=tokens,
        )

    # --- 错题讲解 -----------------------------------------------------------

    def explain_mistake(
        self, question: str, reason: str, chunks: list[Chunk]
    ) -> ExplainResult:
        hits = self.retrieve(chunks, question)
        sources = _sources_of(hits)
        top = hits[0].chunk if hits else None
        text = "\n".join(
            [
                f"错因分析：{reason}",
                f"相关知识点：{top.text}" if top else "本班知识库中暂无直接对应的知识点。",
                "修正建议：请回到定义，逐步重做——先写出关键判断（如判别式或单调性依据），"
                "再得出结论。先自己尝试一次，我可以帮你检查过程是否正确"
                "（这里不直接给出最终答案）。",
            ]
        )
        return ExplainResult(
            text=text, sources=sources, tokens=_estimate_tokens(text), cost_ms=1800
        )

    # --- 学习画像 -----------------------------------------------------------

    def profile(self, data: ProfileInput) -> ProfileResult:
        from app.services.pseudo import stable_hash  # TODO(real-metric)

        ordered = sorted(data.topics, key=lambda t: (-t[1], t[0]))
        strengths = [label for label, _ in ordered[:2]]
        weaknesses = [label for label, _ in ordered[-2:]]
        style = ["稳健推导型", "直觉探索型", "归纳总结型"][
            stable_hash(data.student_name) % 3
        ]
        weakest = weaknesses[-1] if weaknesses else "基础"
        strongest = strengths[0] if strengths else "综合"
        return ProfileResult(
            style=style,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestion=(
                f"建议优先巩固「{weakest}」，围绕本学科讲义要点多做基础题；"
                f"同时保持「{strongest}」的学习手感，形成跨学科的正向迁移。"
            ),
            tags=[style, f"强科·{strongest}", f"待提升·{weakest}"],
        )

    # --- 关怀式对话 ---------------------------------------------------------

    EMOTION_RULES: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
        (
            "焦虑",
            ("焦虑", "紧张", "害怕", "担心", "压力", "慌", "睡不着", "考试"),
            (
                "我能感受到你现在有些紧张和压力。先和我一起做个深呼吸——"
                "吸气 4 秒，屏住 4 秒，再慢慢呼气。",
                "压力往往说明你很在意结果，这本身是件好事。"
                "我们可以把担心的事情一条条写下来，再挑一件现在就能着手的小事去做。",
                "你愿意告诉我，最让你焦虑的是哪一件吗？我们一起把它拆小。",
            ),
        ),
        (
            "低落",
            ("难受", "沮丧", "挫败", "失落", "不会", "放弃", "没用", "差", "哭"),
            (
                "听起来你现在有点低落，辛苦了。遇到难题会让人怀疑自己，"
                "但这并不代表你不够好。",
                "进步很少是直线，一次没做好，只是还没找到适合你的方法。"
                "我们可以从你已经会的那一步重新出发。",
                "如果愿意，说说是哪件事让你有这种感觉？我陪你一起看看下一步可以怎么走。",
            ),
        ),
        (
            "烦躁",
            ("烦", "生气", "讨厌", "累", "受不了", "崩溃"),
            (
                "感觉你现在挺烦、也有点累。先停一停没关系，"
                "情绪需要被看见，而不是被硬压下去。",
                "要不要先离开桌子几分钟，喝口水、走两步？回来后我们再一起，慢一点、一步一步来。",
                "如果你想说说是什么让你烦，我在这里听着。",
            ),
        ),
        (
            "积极",
            ("谢谢", "开心", "加油", "好多了", "懂了", "会了", "太好了", "棒"),
            (
                "真为你高兴！能感觉到你的状态在变好，这份主动和坚持很珍贵。",
                "把这次的好方法记下来，下次遇到类似的题就能更从容。",
                "还有什么想一起聊聊，或者想继续挑战的吗？",
            ),
        ),
    )

    NEUTRAL_REPLY = (
        "谢谢你愿意和我说说。无论是学习还是心情，我都愿意听。\n"
        "我们可以慢慢来——你想先聊聊最近的状态，还是某一件具体的事？"
    )

    HIGH_RISK_KEYWORDS = ("放弃", "崩溃", "哭", "没用", "受不了")

    ESCALATION_TEXT = (
        "\n\n如果这种感觉持续困扰你，别一个人扛着——"
        "可以和信任的老师、家人或同学说说，也可以寻求学校心理老师的帮助。"
        "你值得被认真对待。"
    )

    def detect_emotion(self, text: str) -> CareResult:
        from app.services.pseudo import stable_hash

        matched = next(
            (
                (emotion, replies)
                for emotion, keywords, replies in self.EMOTION_RULES
                if any(k in text for k in keywords)
            ),
            None,
        )
        escalated = any(k in text for k in self.HIGH_RISK_KEYWORDS)

        if matched is None:
            return CareResult(
                emotion="平静",
                reply=self.NEUTRAL_REPLY + (self.ESCALATION_TEXT if escalated else ""),
                escalated=escalated,
            )

        emotion, replies = matched
        lead = replies[stable_hash(text) % len(replies)]
        rest = [r for r in replies if r != lead]
        reply = "\n".join([lead, *rest])
        if escalated:
            reply += self.ESCALATION_TEXT
        return CareResult(emotion=emotion, reply=reply, escalated=escalated)


provider = MockProvider()
