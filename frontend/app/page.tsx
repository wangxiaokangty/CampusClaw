"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useSession } from "@/lib/session";

/** 入口按角色分流。 */
export default function Home() {
  const { me, loading } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!me) router.replace("/login");
    else router.replace(me.user.role === "teacher" ? "/teacher" : "/student");
  }, [me, loading, router]);

  return <div className="empty">正在进入…</div>;
}
