"use client";

/** 教师端 / 学生端共用的外壳：侧边导航 + 身份切换。 */

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { useRequireRole, useSession } from "@/lib/session";
import { Loading } from "@/components/ui";

export interface NavEntry {
  href: string;
  label: string;
  icon: string;
}

export const TEACHER_NAV: NavEntry[] = [
  { href: "/teacher", label: "班级看板", icon: "📊" },
  { href: "/teacher/lectures", label: "讲义与知识库", icon: "📚" },
  { href: "/teacher/assistants", label: "助手配置", icon: "🤖" },
  { href: "/teacher/homework", label: "作业与批改", icon: "📝" },
  { href: "/teacher/audit", label: "技能审计", icon: "🔍" },
];

export const STUDENT_NAV: NavEntry[] = [
  { href: "/student", label: "我的首页", icon: "🏠" },
  { href: "/student/chat", label: "学科助手", icon: "💬" },
  { href: "/student/kb", label: "知识库检索", icon: "🔎" },
  { href: "/student/homework", label: "我的作业", icon: "📝" },
  { href: "/student/mistakes", label: "错题本", icon: "❌" },
  { href: "/student/analytics", label: "学情分析", icon: "📈" },
  { href: "/student/care", label: "心情树洞", icon: "🌱" },
];

export function Shell({ role, children }: { role: "teacher" | "student"; children: ReactNode }) {
  const { me, loading } = useRequireRole(role);
  const { logout } = useSession();
  const pathname = usePathname();
  const nav = role === "teacher" ? TEACHER_NAV : STUDENT_NAV;

  if (loading || !me || me.user.role !== role) return <Loading />;

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          CampusClaw
          <small>{me["class"].name}</small>
        </div>

        <nav className="col" style={{ gap: 2 }}>
          {nav.map((item) => {
            const active =
              pathname === item.href ||
              (item.href !== `/${role}` && pathname.startsWith(`${item.href}/`));
            return (
              <Link key={item.href} href={item.href} className={`nav-item${active ? " active" : ""}`}>
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="identity">
          <div className="who">
            <span className="avatar">{me.user.avatar || "👤"}</span>
            <span style={{ flex: 1 }}>
              <b>{me.user.name}</b>
              <span>{me.user.role === "teacher" ? "教师" : "学生"}</span>
            </span>
          </div>
          <button className="ghost sm" style={{ width: "100%" }} onClick={logout}>
            切换身份
          </button>
        </div>
      </aside>

      <main className="content">{children}</main>
    </div>
  );
}
