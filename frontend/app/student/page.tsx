"use client";

/** 学生首页：本班学科入口与待办概览。 */

import Link from "next/link";
import { useEffect, useState } from "react";

import { apiGet } from "@/lib/api";
import type { Res } from "@/lib/api";
import { errorMessage, useSession } from "@/lib/session";
import { ErrorBanner, Loading, PageHead, Stat } from "@/components/ui";

type Dashboard = Res<"/api/dashboard/student">;

export default function StudentHomePage() {
  const { me } = useSession();
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet("/api/dashboard/student").then(setData).catch((e) => setError(errorMessage(e)));
  }, []);

  if (error) return <ErrorBanner error={error} />;
  if (!data) return <Loading />;

  return (
    <>
      <PageHead
        title={`你好，${me?.user.name ?? ""}`}
        desc={`${data.class_name} · 本班开设 ${data.subjects.length} 个学科`}
      />

      <div className="grid cols-4">
        <Stat label="可用讲义" value={data.lecture_count} />
        <Stat label="作业总数" value={data.homework_count} />
        <Stat label="待提交" value={data.unsubmitted_count} />
        <Stat label="错题" value={data.mistake_count} />
      </div>

      <div className="card" style={{ marginTop: 14 }}>
        <h3>学科助手</h3>
        <div className="row">
          {(me?.subjects ?? []).map((s) => (
            <Link key={s.subject} className="btn" href={`/student/chat?subject=${encodeURIComponent(s.subject)}`}>
              {s.icon} {s.subject}
            </Link>
          ))}
        </div>
      </div>

      <div className="grid cols-3" style={{ marginTop: 14 }}>
        <Link className="card" href="/student/homework">
          <h3>📝 我的作业</h3>
          <p className="muted small" style={{ margin: 0 }}>提交后 AI 异步批改，可观察批改进度</p>
        </Link>
        <Link className="card" href="/student/mistakes">
          <h3>❌ 错题本</h3>
          <p className="muted small" style={{ margin: 0 }}>按错因请求针对性讲解</p>
        </Link>
        <Link className="card" href="/student/analytics">
          <h3>📈 学情分析</h3>
          <p className="muted small" style={{ margin: 0 }}>掌握度、趋势与学习画像</p>
        </Link>
      </div>
    </>
  );
}
