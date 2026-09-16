import type { ReactNode } from "react";

import { Shell } from "@/components/shell";

export default function StudentLayout({ children }: { children: ReactNode }) {
  return <Shell role="student">{children}</Shell>;
}
