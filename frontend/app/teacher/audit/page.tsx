"use client";

/** 技能审计：按技能 / 状态 / 用户过滤的调用留痕，加聚合统计。学生不可访问。 */

import { useCallback, useEffect, useState } from "react";

import { apiGet } from "@/lib/api";
import type { Res } from "@/lib/api";
import { errorMessage } from "@/lib/session";
import { Empty, ErrorBanner, Loading, PageHead, Stat } from "@/components/ui";

type LogPage = Res<"/api/audit/logs">;
type Stats = Res<"/api/audit/stats">;

const PAGE_SIZE = 20;

export default function TeacherAuditPage() {
  const [filters, setFilters] = useState({ skill_key: "", status: "", user_id: "" });
  const [page, setPage] = useState(1);
  const [logs, setLogs] = useState<LogPage | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [users, setUsers] = useState<Res<"/api/users">>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet("/api/audit/stats").then(setStats).catch((e) => setError(errorMessage(e)));
    apiGet("/api/users").then(setUsers).catch(() => undefined);
  }, []);

  const load = useCallback(() => {
    apiGet("/api/audit/logs", {
      query: {
        skill_key: filters.skill_key || undefined,
        status: (filters.status || undefined) as "ok" | "failed" | undefined,
        user_id: filters.user_id || undefined,
        page,
        page_size: PAGE_SIZE,
      },
    })
      .then(setLogs)
      .catch((e) => setError(errorMessage(e)));
  }, [filters, page]);

  useEffect(load, [load]);

  const skillKeys = [...new Set((stats?.by_skill ?? []).map((s) => s.skill_key))];
  const pages = logs ? Math.max(1, Math.ceil(logs.total / logs.page_size)) : 1;

  function setFilter(patch: Partial<typeof filters>) {
    setFilters((f) => ({ ...f, ...patch }));
    setPage(1);
  }

  return (
    <>
      <PageHead title="技能审计" desc="每次 AI 技能调用都留痕：参数为截断摘要，失败调用同样记录。" />
      <ErrorBanner error={error} />

      {stats ? (
        <>
          <div className="grid cols-3">
            <Stat label="总调用次数" value={stats.total_calls} />
            <Stat label="失败率" value={`${(stats.fail_rate * 100).toFixed(1)}%`} />
            <Stat label="总 token 用量" value={stats.total_tokens} />
          </div>

          <div className="card" style={{ marginTop: 14 }}>
            <h3>按技能分项</h3>
            {stats.by_skill.length === 0 ? (
              <Empty>本班尚无审计记录</Empty>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>技能</th>
                    <th>调用</th>
                    <th>失败</th>
                    <th>token</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.by_skill.map((s) => (
                    <tr key={s.skill_key}>
                      <td className="mono">{s.skill_key}</td>
                      <td>{s.calls}</td>
                      <td>{s.failures}</td>
                      <td>{s.tokens}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      ) : null}

      <div className="card" style={{ marginTop: 14 }}>
        <div className="row" style={{ marginBottom: 12 }}>
          <h3 style={{ margin: 0 }}>调用日志</h3>
          <div className="spacer" />
          <select
            style={{ width: 150 }}
            value={filters.skill_key}
            onChange={(e) => setFilter({ skill_key: e.target.value })}
          >
            <option value="">全部技能</option>
            {skillKeys.map((k) => (
              <option key={k} value={k}>
                {k}
              </option>
            ))}
          </select>
          <select
            style={{ width: 120 }}
            value={filters.status}
            onChange={(e) => setFilter({ status: e.target.value })}
          >
            <option value="">全部状态</option>
            <option value="ok">成功</option>
            <option value="failed">失败</option>
          </select>
          <select
            style={{ width: 160 }}
            value={filters.user_id}
            onChange={(e) => setFilter({ user_id: e.target.value })}
          >
            <option value="">全部用户</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name}
              </option>
            ))}
          </select>
        </div>

        {logs === null ? (
          <Loading />
        ) : logs.items.length === 0 ? (
          <Empty>该条件下无审计记录</Empty>
        ) : (
          <>
            <table>
              <thead>
                <tr>
                  <th>时间</th>
                  <th>用户</th>
                  <th>技能</th>
                  <th>动作</th>
                  <th>参数摘要</th>
                  <th>状态</th>
                  <th>耗时</th>
                  <th>token</th>
                </tr>
              </thead>
              <tbody>
                {logs.items.map((l) => (
                  <tr key={l.id}>
                    <td className="small muted">{new Date(l.at).toLocaleString("zh-CN")}</td>
                    <td>{l.user_name}</td>
                    <td className="mono small">{l.skill_key ?? "—"}</td>
                    <td className="small">{l.action}</td>
                    <td className="small muted mono">{l.params}</td>
                    <td>
                      <span className={`tag ${l.status === "ok" ? "ok" : "danger"}`}>
                        {l.status === "ok" ? "成功" : "失败"}
                      </span>
                    </td>
                    <td className="small">{l.cost_ms}ms</td>
                    <td className="small">{l.tokens}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="row" style={{ marginTop: 12 }}>
              <span className="small muted">
                共 {logs.total} 条 · 第 {logs.page} / {pages} 页
              </span>
              <div className="spacer" />
              <button className="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
                上一页
              </button>
              <button className="sm" disabled={page >= pages} onClick={() => setPage(page + 1)}>
                下一页
              </button>
            </div>
          </>
        )}
      </div>
    </>
  );
}
