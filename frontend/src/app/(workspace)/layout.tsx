"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { WorkspaceShell } from "@/components/workspace-shell";
import { useAuth } from "@/features/auth/auth-context";

export default function WorkspaceLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { ready, signedIn } = useAuth();

  useEffect(() => {
    if (ready && !signedIn) router.replace("/login");
  }, [ready, router, signedIn]);

  if (!ready || !signedIn) return null;
  return <WorkspaceShell>{children}</WorkspaceShell>;
}