"use client";

import { type FormEvent, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { useConversations } from "@/features/chat/conversation-context";

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
  const {
    activeConversationId,
    createConversation,
    refreshConversations,
    setActiveConversationId,
  } = useConversations();
  const [historyState, setHistoryState] = useState<{
    conversationId: string;
    messages: Message[];
  } | null>(null);
  const [question, setQuestion] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    if (!activeConversationId) return () => { active = false; };

    void apiRequest<{ history: Message[] }>(
      `/chat/conversations/${encodeURIComponent(activeConversationId)}/messages`,
    )
      .then((result) => {
        if (active) {
          setHistoryState({
            conversationId: activeConversationId,
            messages: result.history ?? [],
          });
          setError("");
        }
      })
      .catch((caught) => {
        if (active) setError(caught instanceof Error ? caught.message : "Unable to load chat history.");
      });

    return () => { active = false; };
  }, [activeConversationId]);

  const historyIsCurrent = activeConversationId !== null
    && historyState?.conversationId === activeConversationId;
  const messages = historyIsCurrent ? historyState.messages : [];
  const loadingHistory = activeConversationId !== null && !historyIsCurrent;

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = question.trim();
    if (!message || busy) return;

    setQuestion("");
    setError("");
    setBusy(true);
    let conversationId = activeConversationId;
    const isNewConversation = conversationId === null;
    try {
      if (!conversationId) {
        const conversation = await createConversation(false);
        conversationId = conversation.id;
        setHistoryState({ conversationId, messages: [] });
      }

      const targetConversationId = conversationId;
      setHistoryState((current) => ({
        conversationId: targetConversationId,
        messages: current?.conversationId === targetConversationId
          ? [...current.messages, { role: "user", content: message }]
          : [{ role: "user", content: message }],
      }));
      const result = await apiRequest<{ response: string; citations: Citation[] }>(
        `/chat/conversations/${encodeURIComponent(targetConversationId)}/messages`,
        {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
        },
      );
      setHistoryState((current) => current?.conversationId === targetConversationId
        ? {
          ...current,
          messages: [...current.messages, {
            role: "assistant",
            content: result.response || "No answer was returned.",
            citations: result.citations ?? [],
          }],
        }
        : current);
      if (isNewConversation) {
        setActiveConversationId((current) => current ?? targetConversationId);
      }
      try {
        await refreshConversations();
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Unable to refresh the chat list.");
      }
    } catch (caught) {
      if (conversationId && conversationId !== activeConversationId) {
        setActiveConversationId(conversationId);
      }
      setError(caught instanceof Error ? caught.message : "Unable to reach the assistant.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader eyebrow="Workspace" title="Ask your knowledge" description="Answers are based on the documents available to you." />
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
          <textarea aria-label="Your question" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask anything about your documents..." rows={1} disabled={loadingHistory || busy} />
          <button className="primary" disabled={busy || loadingHistory || !question.trim()}>{busy ? "Thinking..." : "Ask"}</button>
        </form>
      </section>
    </>
  );
}