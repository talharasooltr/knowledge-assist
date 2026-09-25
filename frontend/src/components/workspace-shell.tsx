"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useAuth } from "@/features/auth/auth-context";

const navigation = [
  { href: "/chat", label: "Ask knowledge" },
  { href: "/documents", label: "Documents" },
];

export function WorkspaceShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { role, username, signOut } = useAuth();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand" href="/chat"><span className="brand-mark">◈</span> Knowledge Assistant</Link>
        <div className="sidebar-user"><strong>{username}</strong><br />{role === "admin" ? "Administrator" : "Member"}</div>
        <nav className="nav" aria-label="Workspace">
          {navigation.map((item) => <Link className={pathname === item.href ? "active" : ""} href={item.href} key={item.href}>{item.label}</Link>)}
          {role === "admin" && <Link className={pathname.startsWith("/admin/users") ? "active" : ""} href="/admin/users">People</Link>}
        </nav>
        <button className="signout" onClick={signOut} type="button">Sign out</button>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}