"use client";

/** 选人登录（design.md D7）：点账号即切换身份，用于演示班级隔离与角色差异。 */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { apiGet } from "@/lib/api";
import type { Res } from "@/lib/api";
import { errorMessage, useSession } from "@/lib/session";
import { ErrorBanner, Loading } from "@/components/ui";

type Account = Res<"/api/users">[number];

export default function LoginPage() {
  const [accounts, setAccounts] = useState<Account[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<string | null>(null);
  const { login } = useSession();
  const router = useRouter();

  useEffect(() => {
    apiGet("/api/users").then(setAccounts).catch((e) => setError(errorMessage(e)));
  }, []);

  async function pick(id: string) {
    setPending(id);
    setError(null);
    try {
      const me = await login(id);
      router.replace(me.user.role === "teacher" ? "/teacher" : "/student");
    } catch (e) {
      setError(errorMessage(e));
      setPending(null);
    }
  }

  const byClass = new Map<string, Account[]>();
  for (const a of accounts ?? []) {
    const key = a.class_name || a.class_id;
    byClass.set(key, [...(byClass.get(key) ?? []), a]);
  }

  return (
    <div className="login-page">
      <div className="card login-card col">
        <div>
          <h1 style={{ margin: 0, fontSize: 22 }}>CampusClaw</h1>
          <p className="muted" style={{ margin: "4px 0 0" }}>
            选择一个身份进入。不同班级之间的数据互不可见，教师与学生的权限不同。
          </p>
        </div>

        <ErrorBanner error={error} />

        {accounts === null ? (
          <Loading />
        ) : (
          [...byClass.entries()].map(([className, list]) => (
            <div key={className} className="col" style={{ gap: 6 }}>
              <div className="small muted">{className}</div>
              {list.map((a) => (
                <button
                  key={a.id}
                  className="account"
                  disabled={pending !== null}
                  onClick={() => pick(a.id)}
                >
                  <span className="avatar">{a.avatar || "👤"}</span>
                  <span style={{ flex: 1 }}>
                    <b>{a.name}</b>
                    <span className="small muted">
                      {a.role === "teacher" ? "教师" : "学生"} · {a.class_name || a.class_id}
                    </span>
                  </span>
                  <span className="small muted">{pending === a.id ? "进入中…" : "进入 →"}</span>
                </button>
              ))}
            </div>
          ))
        )}

        <p className="small muted" style={{ margin: 0 }}>
          演示用登录：不校验密码，不适用于生产环境。
        </p>
      </div>
    </div>
  );
}
