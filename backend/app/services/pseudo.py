"""确定性伪随机指标（design.md D8）。

演示中一部分学情数值不是算出来的，而是由姓名/学科哈希生成的。
本阶段照搬这些函数以保证图表数值稳定且视觉合理；每一处都标注
TODO(real-metric)，构成一份明确的待偿清单。

约束：必须是确定性的——相同输入恒产生相同输出。
"""


def stable_hash(text: str) -> int:
    """与演示前端一致的字符串哈希，保证跨端数值相同。"""
    value = 0
    for ch in text:
        value = (value * 31 + ord(ch)) % 100_000
    return value


def topic_baseline(student_id: str, subject: str) -> int:
    """TODO(real-metric): 学科掌握度基准值，应由真实答题正确率替代。"""
    return min(96, 58 + stable_hash(f"{student_id}::{subject}") % 38)


# TODO(real-metric): 成绩趋势的历史段，应由真实历史成绩替代。
PROGRESS_HISTORY: tuple[int, ...] = (68, 74, 71, 82, 79)

# TODO(real-metric): 班级近七日活跃度，应由真实审计时间分布替代。
CLASS_ACTIVITY: tuple[int, ...] = (12, 18, 9, 24, 30, 21, 34)

MISTAKE_PENALTY = 16
"""每条错题对该学科掌握度的扣减，下限 35。"""

MASTERY_FLOOR = 35
