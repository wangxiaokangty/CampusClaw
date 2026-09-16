"""学情分析的接口形状。

标注 [演示数据] 的字段为确定性模拟值（design.md D8），
相同输入恒产生相同输出，但不来自真实行为数据。
"""

from pydantic import BaseModel, Field


class TopicScore(BaseModel):
    label: str
    value: int = Field(description="[演示数据] 学科掌握度基准值")


class StudentStats(BaseModel):
    questions: int = Field(description="提问次数，取自真实审计记录")
    submissions: int = Field(description="提交份数，真实值")
    accuracy: int = Field(description="正确率百分比，真实值")
    mistakes: int = Field(description="错题数，真实值")


class LearnerProfile(BaseModel):
    style: str = Field(description="[演示数据] 学习风格")
    strengths: list[str] = []
    weaknesses: list[str] = []
    suggestion: str = ""
    tags: list[str] = []


class StudentAnalytics(BaseModel):
    topics: list[TopicScore]
    progress: list[int] = Field(description="[演示数据] 历史段 + 真实已批改分数")
    overall: int
    stats: StudentStats
    profile: LearnerProfile


class ClassAnalytics(BaseModel):
    topics: list[TopicScore]
    overall: int
    activity: list[int] = Field(description="[演示数据] 近七日活跃度")
    student_count: int = Field(description="真实值")
    skill_calls: int = Field(description="技能调用总次数，取自真实审计记录")


class TeacherDashboard(BaseModel):
    class_id: str
    class_name: str
    subjects: list[str]
    lecture_count: int
    homework_count: int
    pending_submissions: int
    analytics: ClassAnalytics


class StudentDashboard(BaseModel):
    class_id: str
    class_name: str
    subjects: list[str]
    lecture_count: int
    homework_count: int
    unsubmitted_count: int
    mistake_count: int
