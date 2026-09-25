"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/features/auth/auth-context";

export default function AdminLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { ready, role } = useAuth();

  useEffect(() => {
    if (ready && role !== "admin") router.replace("/chat");
  }, [ready, role, router]);

  if (!ready || role !== "admin") return null;
  return children;
}