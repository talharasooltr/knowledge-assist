"use client";

import { type FormEvent, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/features/auth/auth-context";

type Citation = { number: number; filename: string; page: number | null };
type Message = { role: "user" | "assistant"; content: string; citations?: Citation[] };

function renderAnswer(content: string, citations: Citation[], messageIndex: number) {
  const parts = content.split(/(\[\d+\])/g);
  return parts.map((part, index) => {
    const match = part.match(/^\[(\d+)\]$/);
    const number = match ? Number(match[1]) : null;
    if (number !== null && citations.some((citation) => citation.number === number)) {
      return <a className="citation-reference" href={`#citation-${messageIndex}-${number}`} key={index}>{part}</a>;
    }
    return part;
  });
}

export default function ChatPage() {
  const { auth, role, username, ready } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);

  useEffect(() => {
    let active = true;
    if (!ready) return () => { active = false; };
    if (!auth) {
      setMessages([]);
      setLoadingHistory(false);
      return () => { active = false; };
    }

    setLoadingHistory(true);
    setError("");
    const historyPath = role === "user"
      ? "/user/chat/history"
      : `/admin/chat/history/${encodeURIComponent(username)}`;
    void apiRequest<{ history: Message[] }>(historyPath, auth)
      .then((result) => {
        if (active) setMessages(result.history ?? []);
      })
      .catch((caught) => {
        if (active) setError(caught instanceof Error ? caught.message : "Unable to load chat history.");
      })
      .finally(() => {
        if (active) setLoadingHistory(false);
      });

    return () => { active = false; };
  }, [auth, ready, role, username]);

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = question.trim();
    if (!message || busy) return;

    setQuestion("");
    setError("");
    setMessages((current) => [...current, { role: "user", content: message }]);
    setBusy(true);
    try {
      const result = await apiRequest<{ response: string; citations: Citation[] }>(`/${role}/chat`, auth, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: username, message }),
      });
      setMessages((current) => [...current, {
        role: "assistant",
        content: result.response || "No answer was returned.",
        citations: result.citations ?? [],
      }]);
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
          {loadingHistory ? (
            <div className="empty"><div>Loading conversation...</div></div>
          ) : messages.length === 0 ? (
            <div className="empty"><div><strong>What would you like to know?</strong>Ask a question about your indexed documents.</div></div>
          ) : messages.map((item, index) => (
            <div className={`message-group ${item.role}`} key={`${item.role}-${index}`}>
              <div className={`message ${item.role}`}>
                {item.role === "assistant" ? renderAnswer(item.content, item.citations ?? [], index) : item.content}
              </div>
              {item.role === "assistant" && item.citations && item.citations.length > 0 && (
                <div className="citation-list" aria-label="Answer sources">
                  {item.citations.map((citation) => (
                    <span
                      className="citation-item"
                      id={`citation-${index}-${citation.number}`}
                      key={`${citation.number}-${citation.filename}-${citation.page}`}
                    >
                      <span className="citation-number">[{citation.number}]</span>
                      <span>{citation.filename}{citation.page ? ` · p. ${citation.page}` : ""}</span>
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
        <form className="chat-form" onSubmit={sendMessage}>
          <textarea aria-label="Your question" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask anything about your documents..." rows={1} disabled={loadingHistory} />
          <button className="primary" disabled={busy || loadingHistory || !question.trim()}>{busy ? "Thinking..." : "Ask"}</button>
        </form>
      </section>
    </>
  );
}