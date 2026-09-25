"use client";

import { type FormEvent, useState } from "react";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/features/auth/auth-context";

type Message = { role: "user" | "assistant"; content: string };

export default function ChatPage() {
  const { auth, role, username } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = question.trim();
    if (!message || busy) return;

    setQuestion("");
    setError("");
    setMessages((current) => [...current, { role: "user", content: message }]);
    setBusy(true);
    try {
      const result = await apiRequest<{ response: string }>(`/${role}/chat`, auth, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: username, message }),
      });
      setMessages((current) => [...current, { role: "assistant", content: result.response || "No answer was returned." }]);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to reach the assistant.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <header className="topline">
        <div><div className="eyebrow">Knowledge workspace</div><h1>Ask your knowledge</h1><div className="subtle">Find answers across the information your team has collected.</div></div>
      </header>
      {error && <div className="error" role="alert">{error}</div>}
      <section className="panel chat-panel">
        <div className="chat-list" aria-live="polite">
          {messages.length === 0 ? (
            <div className="empty"><div><strong>What would you like to know?</strong>Ask a question about your indexed documents.</div></div>
          ) : messages.map((item, index) => (
            <div className={`message ${item.role}`} key={`${item.role}-${index}`}>{item.content}</div>
          ))}
        </div>
        <form className="chat-form" onSubmit={sendMessage}>
          <textarea aria-label="Your question" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask anything about your documents..." rows={1} />
          <button className="primary" disabled={busy || !question.trim()}>{busy ? "Thinking..." : "Ask"}</button>
        </form>
      </section>
    </>
  );
}