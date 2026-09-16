import type { ReactNode } from "react";

import { Shell } from "@/components/shell";

export default function TeacherLayout({ children }: { children: ReactNode }) {
  return <Shell role="teacher">{children}</Shell>;
}
