"use client";

/** 页面共用的展示件。 */

import type { ReactNode } from "react";

export function PageHead({ title, desc, actions }: { title: string; desc?: string; actions?: ReactNode }) {
  return (
    <div className="page-head row">
      <div>
        <h1>{title}</h1>
        {desc ? <p>{desc}</p> : null}
      </div>
      <div className="spacer" />
      {actions}
    </div>
  );
}

export function Stat({ label, value, hint }: { label: string; value: ReactNode; hint?: string }) {
  return (
    <div className="card stat">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
      {hint ? <div className="small muted">{hint}</div> : null}
    </div>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="empty">{children}</div>;
}

export function Loading() {
  return <div className="empty">加载中…</div>;
}

export function ErrorBanner({ error }: { error: string | null }) {
  if (!error) return null;
  return <div className="banner">{error}</div>;
}

/** 演示数据标注：确定性模拟值，不来自真实行为数据（design.md D8）。 */
export function DemoBadge() {
  return <span className="tag warn" title="确定性模拟值，非真实行为数据">演示数据</span>;
}

export function SubjectFilter({
  subjects,
  value,
  onChange,
}: {
  subjects: string[];
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      style={{ width: 150 }}
      aria-label="按学科过滤"
    >
      <option value="">全部学科</option>
      {subjects.map((s) => (
        <option key={s} value={s}>
          {s}
        </option>
      ))}
    </select>
  );
}

/** 掌握度条形图——雷达的可读替代，同样只读 topics。 */
export function TopicBars({ topics }: { topics: { label: string; value: number }[] }) {
  if (!topics.length) return <Empty>暂无学科数据</Empty>;
  return (
    <div className="col">
      {topics.map((t) => (
        <div key={t.label}>
          <div className="row small">
            <span>{t.label}</span>
            <div className="spacer" />
            <span className="muted">{t.value}</span>
          </div>
          <div className="bar">
            <i style={{ width: `${Math.max(0, Math.min(100, t.value))}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

/** 折线的可读替代：等宽柱状序列。 */
export function Sparkbars({ values, suffix = "" }: { values: number[]; suffix?: string }) {
  if (!values.length) return <Empty>暂无数据</Empty>;
  const max = Math.max(...values, 1);
  return (
    <div className="row" style={{ alignItems: "flex-end", height: 110, gap: 8 }}>
      {values.map((v, i) => (
        <div key={i} style={{ flex: 1, textAlign: "center" }}>
          <div
            title={`${v}${suffix}`}
            style={{
              height: `${(v / max) * 84}px`,
              background: "var(--brand)",
              borderRadius: "5px 5px 0 0",
              opacity: 0.35 + (0.65 * v) / max,
            }}
          />
          <div className="small muted">{v}</div>
        </div>
      ))}
    </div>
  );
}
