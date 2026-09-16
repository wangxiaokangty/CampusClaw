"use client";

/** 教师班级看板：讲义/作业/待批概览 + 班级统计。 */

import { useEffect, useState } from "react";

import { apiGet } from "@/lib/api";
import type { Res } from "@/lib/api";
import { errorMessage } from "@/lib/session";
import { DemoBadge, ErrorBanner, Loading, PageHead, Sparkbars, Stat, TopicBars } from "@/components/ui";

type Dashboard = Res<"/api/dashboard/teacher">;

export default function TeacherDashboardPage() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet("/api/dashboard/teacher").then(setData).catch((e) => setError(errorMessage(e)));
  }, []);

  if (error) return <ErrorBanner error={error} />;
  if (!data) return <Loading />;

  const a = data.analytics;

  return (
    <>
      <PageHead title="班级看板" desc={`${data.class_name} · 已开设 ${data.subjects.length} 个学科`} />

      <div className="grid cols-4">
        <Stat label="讲义" value={data.lecture_count} hint="本班知识库来源" />
        <Stat label="作业" value={data.homework_count} />
        <Stat label="待终评提交" value={data.pending_submissions} hint="尚无教师改分" />
        <Stat label="学生人数" value={a.student_count} />
      </div>

      <div className="grid cols-2" style={{ marginTop: 14 }}>
        <div className="card">
          <h3>
            班级学科掌握分布 <DemoBadge />
          </h3>
          <TopicBars topics={a.topics} />
          <p className="small muted" style={{ marginBottom: 0 }}>
            综合得分 {a.overall}
          </p>
        </div>

        <div className="card">
          <h3>
            近七日活跃度 <DemoBadge />
          </h3>
          <Sparkbars values={a.activity} />
          <p className="small muted" style={{ marginBottom: 0 }}>
            技能调用总次数 <b>{a.skill_calls}</b>（取自真实审计记录）
          </p>
        </div>
      </div>

      <div className="card" style={{ marginTop: 14 }}>
        <h3>本班学科</h3>
        <div className="row">
          {data.subjects.map((s) => (
            <span key={s} className="tag brand">
              {s}
            </span>
          ))}
        </div>
      </div>
    </>
  );
}
