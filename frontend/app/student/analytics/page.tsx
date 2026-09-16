"use client";

/** 学情分析：掌握度、趋势、统计摘要与学习画像。标注哪些是真实值、哪些是演示数据。 */

import { useEffect, useState } from "react";

import { apiGet } from "@/lib/api";
import type { Res } from "@/lib/api";
import { errorMessage } from "@/lib/session";
import {
  DemoBadge,
  ErrorBanner,
  Loading,
  PageHead,
  Sparkbars,
  Stat,
  TopicBars,
} from "@/components/ui";

type Analytics = Res<"/api/analytics/student/me">;

export default function StudentAnalyticsPage() {
  const [data, setData] = useState<Analytics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet("/api/analytics/student/me").then(setData).catch((e) => setError(errorMessage(e)));
  }, []);

  if (error) return <ErrorBanner error={error} />;
  if (!data) return <Loading />;

  return (
    <>
      <PageHead
        title="学情分析"
        desc="提交数、正确率、错题数为真实值；掌握度基准、趋势历史段与学习风格为确定性演示数据。"
      />

      <div className="grid cols-4">
        <Stat label="提问次数" value={data.stats.questions} hint="取自真实审计记录" />
        <Stat label="提交份数" value={data.stats.submissions} hint="真实值" />
        <Stat label="正确率" value={`${data.stats.accuracy}%`} hint="已批改且未判错的占比" />
        <Stat label="错题数" value={data.stats.mistakes} hint="真实值" />
      </div>

      <div className="grid cols-2" style={{ marginTop: 14 }}>
        <div className="card">
          <h3>
            学科掌握度 <DemoBadge />
          </h3>
          <TopicBars topics={data.topics} />
          <p className="small muted" style={{ marginBottom: 0 }}>
            综合得分 {data.overall} · 存在错题的学科掌握度会被拉低
          </p>
        </div>

        <div className="card">
          <h3>
            成绩趋势 <DemoBadge />
          </h3>
          <Sparkbars values={data.progress} />
          <p className="small muted" style={{ marginBottom: 0 }}>
            历史段为演示数据，末段为真实的已批改分数
          </p>
        </div>
      </div>

      <div className="card" style={{ marginTop: 14 }}>
        <h3>
          学习画像 <DemoBadge />
        </h3>
        <div className="row" style={{ marginBottom: 10 }}>
          <span className="tag brand">{data.profile.style}</span>
          {data.profile.tags
            .filter((t) => t !== data.profile.style)
            .map((t) => (
              <span key={t} className="tag">
                {t}
              </span>
            ))}
        </div>
        <div className="grid cols-2">
          <div>
            <div className="small muted">优势知识点</div>
            {data.profile.strengths.length ? (
              <ul style={{ margin: "4px 0 0", paddingLeft: 18 }}>
                {data.profile.strengths.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
            ) : (
              <p className="small muted">暂无</p>
            )}
          </div>
          <div>
            <div className="small muted">待提升知识点</div>
            {data.profile.weaknesses.length ? (
              <ul style={{ margin: "4px 0 0", paddingLeft: 18 }}>
                {data.profile.weaknesses.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
            ) : (
              <p className="small muted">暂无</p>
            )}
          </div>
        </div>
        {data.profile.suggestion ? (
          <div className="notice" style={{ marginTop: 12 }}>
            {data.profile.suggestion}
          </div>
        ) : null}
      </div>
    </>
  );
}
