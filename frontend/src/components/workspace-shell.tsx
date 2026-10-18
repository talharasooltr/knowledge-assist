"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type ReactNode } from "react";
import { useAuth } from "@/features/auth/auth-context";

const navigation = [
  { href: "/chat", label: "Ask knowledge" },
  { href: "/documents", label: "Documents" },
];

export function WorkspaceShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { role, username, signOut } = useAuth();
  const [error, setError] = useState("");

  async function handleSignOut() {
    setError("");
    try {
      await signOut();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to sign out.");
    }
  }

  return (
    <div className={`app-shell ${pathname === "/chat" ? "app-shell-chat" : ""}`}>
      <aside className="sidebar">
        <Link className="brand" href="/chat"><span className="brand-mark">◈</span> Knowledge Assistant</Link>
        <div className="sidebar-user"><strong>{username}</strong><br />{role === "admin" ? "Administrator" : "Member"}</div>
        <nav className="nav" aria-label="Workspace">
          {navigation.map((item) => <Link className={pathname === item.href ? "active" : ""} href={item.href} key={item.href}>{item.label}</Link>)}
          {role === "admin" && <Link className={pathname.startsWith("/admin/users") ? "active" : ""} href="/admin/users">People</Link>}
        </nav>
        {error && <div className="error" role="alert">{error}</div>}
        <button className="signout" onClick={() => void handleSignOut()} type="button">Sign out</button>
      </aside>
      <main className={`main ${pathname === "/chat" ? "main-chat" : ""} ${pathname === "/documents" ? "main-documents" : ""} ${pathname.startsWith("/admin/users") ? "main-people" : ""}`}>{children}</main>
    </div>
  );
}