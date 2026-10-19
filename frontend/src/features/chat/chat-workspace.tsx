"use client";

import { type FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest } from "@/lib/api";
import { useConversations } from "@/features/chat/conversation-context";

type Citation = {
  number: number;
  filename: string;
  page: number | null;
  page_end?: number | null;
  section?: string | null;
};
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

export function ChatWorkspace({ conversationId }: { conversationId: string | null }) {
  const router = useRouter();
  const {
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
  const [historyFailedConversationId, setHistoryFailedConversationId] = useState<string | null>(null);
  const [historyRequestVersion, setHistoryRequestVersion] = useState(0);
  const [pendingConversationId, setPendingConversationId] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    if (!conversationId) return () => { active = false; };

    void apiRequest<{ history: Message[] }>(
      `/chat/conversations/${encodeURIComponent(conversationId)}/messages`,
    )
      .then((result) => {
        if (active) {
          setHistoryState({
            conversationId,
            messages: result.history ?? [],
          });
          setHistoryFailedConversationId(null);
          setError("");
        }
      })
      .catch((caught) => {
        if (active) {
          setHistoryFailedConversationId(conversationId);
          setError(caught instanceof Error ? caught.message : "Unable to load this chat.");
        }
      });

    return () => { active = false; };
  }, [conversationId, historyRequestVersion]);

  const historyIsCurrent = conversationId !== null
    && historyState?.conversationId === conversationId;
  const messages = historyIsCurrent ? historyState.messages : [];
  const historyLoadFailed = conversationId !== null
    && historyFailedConversationId === conversationId;
  const loadingHistory = conversationId !== null && !historyIsCurrent && !historyLoadFailed;
  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = question.trim();
    if (!message || busy) return;

    setQuestion("");
    setError("");
    setBusy(true);
    const isNewConversation = conversationId === null;
    let targetConversationId = conversationId ?? pendingConversationId;

    try {
      if (!targetConversationId) {
        const conversation = await createConversation(false);
        targetConversationId = conversation.id;
        setPendingConversationId(conversation.id);
      }

      const targetId = targetConversationId;
      setHistoryState((current) => ({
        conversationId: targetId,
        messages: current?.conversationId === targetId
          ? [...current.messages, { role: "user", content: message }]
          : [{ role: "user", content: message }],
      }));
      const result = await apiRequest<{ response: string; citations: Citation[] }>(
        `/chat/conversations/${encodeURIComponent(targetId)}/messages`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message }),
        },
      );
      setHistoryState((current) => current?.conversationId === targetId
        ? {
          ...current,
          messages: [...current.messages, {
            role: "assistant",
            content: result.response || "No answer was returned.",
            citations: result.citations ?? [],
          }],
        }
        : current);
      if (isNewConversation) setPendingConversationId(null);
      try {
        await refreshConversations();
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Unable to refresh the chat list.");
      }
      if (isNewConversation) {
        setActiveConversationId(targetId);
        router.replace(`/chat/${targetId}`);
      }
    } catch (caught) {
      if (targetConversationId) {
        setHistoryState((current) => {
          if (current?.conversationId !== targetConversationId) return current;
          const lastMessage = current.messages[current.messages.length - 1];
          return lastMessage?.role === "user" && lastMessage.content === message
            ? { ...current, messages: current.messages.slice(0, -1) }
            : current;
        });
      }
      setQuestion(message);
      setError(caught instanceof Error ? caught.message : "Unable to send your message.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      {error && <div className="error" role="alert">{error}</div>}
      <section className="chat-panel">
        <div className="chat-list" aria-live="polite">
          {loadingHistory ? (
            <div className="empty"><div>Loading chat...</div></div>
          ) : historyLoadFailed ? (
            <div className="empty">
              <div>
                <strong>Could not load this chat.</strong>
                <button
                  className="secondary"
                  onClick={() => {
                    setHistoryFailedConversationId(null);
                    setHistoryRequestVersion((version) => version + 1);
                  }}
                  type="button"
                >
                  Try again
                </button>
              </div>
            </div>
          ) : messages.length === 0 ? (
            <div className="empty">
              <div>
                <strong>What would you like to know?</strong>
                Ask a question about your documents.
              </div>
            </div>
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
                      key={`${citation.number}-${citation.filename}-${citation.page}-${citation.section ?? ""}`}
                    >
                      <span className="citation-number">[{citation.number}]</span>
                      <span>
                        {citation.filename}
                        {citation.page
                          ? ` · p. ${citation.page}${citation.page_end && citation.page_end !== citation.page ? `–${citation.page_end}` : ""}`
                          : ""}
                        {citation.section ? ` · ${citation.section}` : ""}
                      </span>
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
        <form className="chat-form" onSubmit={sendMessage}>
          <textarea
            aria-label="Your question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask anything about your documents..."
            rows={1}
            disabled={loadingHistory || historyLoadFailed || busy}
          />
          <button
            aria-label={busy ? "Thinking..." : "Send message"}
            className="chat-send"
            disabled={busy || loadingHistory || historyLoadFailed || !question.trim()}
            type="submit"
          >
            <svg aria-hidden="true" fill="none" height="18" viewBox="0 0 24 24" width="18">
              <path
                d="M12 19V5m-7 7 7-7 7 7"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
              />
            </svg>
          </button>
        </form>
      </section>
    </>
  );
}
