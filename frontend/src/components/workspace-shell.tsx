"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type ReactNode } from "react";
import { useAuth } from "@/features/auth/auth-context";
import { useRouter } from "next/navigation";
import { useConversations } from "@/features/chat/conversation-context";

const navigation = [
  { href: "/documents", label: "Documents" },
];

export function WorkspaceShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { role, username, signOut } = useAuth();
  const [error, setError] = useState("");
  const {
    conversations,
    activeConversationId,
    setActiveConversationId,
    startNewChat,
    deleteConversation,
    error: conversationError,
    clearError,
  } = useConversations();

  async function handleSignOut() {
    setError("");
    try {
      await signOut();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to sign out.");
    }
  }

  function handleNewChat() {
    setError("");
    startNewChat();
    router.push("/chat");
  }

  async function handleDeleteConversation(id: string, title: string) {
    if (!window.confirm(`Delete "${title}"? This cannot be undone.`)) return;
    setError("");
    try {
      const remaining = conversations.filter((conversation) => conversation.id !== id);
      await deleteConversation(id);
      if (pathname === `/chat/${id}`) {
        if (remaining.length > 0) {
          setActiveConversationId(remaining[0].id);
          router.replace(`/chat/${remaining[0].id}`);
        } else {
          startNewChat();
          router.replace("/chat");
        }
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to delete this chat.");
    }
  }

  const pathConversationId = pathname.startsWith("/chat/")
    ? pathname.slice("/chat/".length).split("/")[0]
    : null;
  const selectedConversationId = pathConversationId ?? activeConversationId;
  const isNewChat = pathname === "/chat";

  return (
    <div className={`app-shell ${pathname.startsWith("/chat") ? "app-shell-chat" : ""}`}>
      <aside className="sidebar">
        <Link className="brand" href="/chat" onClick={startNewChat}><span className="brand-mark" aria-hidden="true">K</span><span>Knowledge Assistant</span></Link>
        <div className="sidebar-user">
          <span className="avatar" aria-hidden="true">{username.slice(0, 1).toUpperCase()}</span>
          <span><strong>{username}</strong><small>{role === "admin" ? "Administrator" : "Member"}</small></span>
        </div>
        <nav className="nav" aria-label="Workspace">
          <button className={`new-chat-button ${isNewChat ? "active" : ""}`} onClick={handleNewChat} type="button">
            <span aria-hidden="true">+</span> New chat
          </button>
          {navigation.map((item) => <Link className={pathname === item.href ? "active" : ""} href={item.href} key={item.href}>{item.label}</Link>)}
          {role === "admin" && <Link className={pathname.startsWith("/admin/users") ? "active" : ""} href="/admin/users">People</Link>}
        </nav>
        <section className="conversation-section" aria-label="Recent conversations">
          <div className="conversation-heading">Recent</div>
          <div className="conversation-list">
            {conversations.map((conversation) => (
              <div className={`conversation-row ${selectedConversationId === conversation.id ? "active" : ""}`} key={conversation.id}>
                <button
                  className="conversation-select"
                  onClick={() => {
                    clearError();
                    setActiveConversationId(conversation.id);
                    router.push(`/chat/${conversation.id}`);
                  }}
                  title={conversation.title}
                  type="button"
                >
                  {conversation.title}
                </button>
                <button
                  aria-label={`Delete ${conversation.title}`}
                  className="conversation-delete"
                  onClick={() => void handleDeleteConversation(conversation.id, conversation.title)}
                  type="button"
                >
                  ×
                </button>
              </div>
            ))}
            {conversations.length === 0 && !conversationError && (
              <div className="conversation-empty">Your chats will appear here.</div>
            )}
          </div>
        </section>
        {(error || conversationError) && <div className="error" role="alert">{error || conversationError}</div>}
        <button className="signout" onClick={() => void handleSignOut()} type="button">Sign out</button>
      </aside>
      <main className={`main ${pathname.startsWith("/chat") ? "main-chat" : ""} ${pathname === "/documents" ? "main-documents" : ""} ${pathname.startsWith("/admin/users") ? "main-people" : ""}`}>{children}</main>
    </div>
  );
}