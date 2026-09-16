"use client";

/** 会话状态：JWT 与当前用户上下文。切换身份即重新登录（design.md D7）。 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";

import { apiGet, apiPost, getToken, setToken, ApiError } from "@/lib/api";
import type { Res } from "@/lib/api";

type Me = Res<"/api/auth/me">;

interface SessionValue {
  me: Me | null;
  loading: boolean;
  login: (userId: string) => Promise<Me>;
  logout: () => void;
}

const Ctx = createContext<SessionValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    if (!getToken()) {
      setLoading(false);
      return;
    }
    apiGet("/api/auth/me")
      .then(setMe)
      .catch(() => setToken(null))
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (userId: string) => {
    const res = await apiPost("/api/auth/login", { user_id: userId });
    setToken(res.access_token);
    const next = await apiGet("/api/auth/me");
    setMe(next);
    return next;
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setMe(null);
    router.push("/login");
  }, [router]);

  const value = useMemo(() => ({ me, loading, login, logout }), [me, loading, login, logout]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useSession(): SessionValue {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useSession 必须在 SessionProvider 内使用");
  return ctx;
}

/** 受保护页面的统一入口：未登录跳转登录页，角色不符跳回本方首页。 */
export function useRequireRole(role?: "teacher" | "student") {
  const { me, loading } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!me) {
      router.replace("/login");
      return;
    }
    if (role && me.user.role !== role) {
      router.replace(me.user.role === "teacher" ? "/teacher" : "/student");
    }
  }, [me, loading, role, router]);

  return { me, loading };
}

export function errorMessage(e: unknown): string {
  if (e instanceof ApiError) return e.detail;
  return e instanceof Error ? e.message : String(e);
}
