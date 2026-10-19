"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
  type Dispatch,
  type SetStateAction,
} from "react";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/features/auth/auth-context";

export type ChatConversation = {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
};

type ConversationContextValue = {
  conversations: ChatConversation[];
  activeConversationId: string | null;
  draftVersion: number;
  setActiveConversationId: Dispatch<SetStateAction<string | null>>;
  startNewChat: () => void;
  createConversation: (activate?: boolean) => Promise<ChatConversation>;
  deleteConversation: (id: string) => Promise<void>;
  refreshConversations: () => Promise<ChatConversation[]>;
  error: string;
  clearError: () => void;
};

const ConversationContext = createContext<ConversationContextValue | null>(null);

export function ConversationProvider({ children }: { children: ReactNode }) {
  const { ready, signedIn } = useAuth();
  const [conversations, setConversations] = useState<ChatConversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [draftVersion, setDraftVersion] = useState(0);
  const [error, setError] = useState("");

  const refreshConversations = useCallback(async () => {
    const result = await apiRequest<{ conversations: ChatConversation[] }>("/chat/conversations");
    setConversations(result.conversations);
    return result.conversations;
  }, []);

  const clearError = useCallback(() => setError(""), []);

  const startNewChat = useCallback(() => {
    setActiveConversationId(null);
    setDraftVersion((current) => current + 1);
    setError("");
  }, []);

  const createConversation = useCallback(async (activate = true) => {
    const conversation = await apiRequest<ChatConversation>("/chat/conversations", {
      method: "POST",
    });
    setConversations((current) => [conversation, ...current]);
    if (activate) setActiveConversationId(conversation.id);
    setError("");
    return conversation;
  }, []);

  const deleteConversation = useCallback(async (id: string) => {
    await apiRequest(`/chat/conversations/${encodeURIComponent(id)}`, {
      method: "DELETE",
    });
    const remaining = conversations.filter((conversation) => conversation.id !== id);
    setConversations(remaining);
    setActiveConversationId((activeId) => (
      activeId === id ? remaining[0]?.id ?? null : activeId
    ));
  }, [conversations]);

  useEffect(() => {
    if (!ready || !signedIn) return;
    let active = true;
    void apiRequest<{ conversations: ChatConversation[] }>("/chat/conversations")
      .then(({ conversations: loaded }) => {
        if (active) {
          setConversations((current) => {
            const loadedIds = new Set(loaded.map((conversation) => conversation.id));
            return [
              ...current.filter((conversation) => !loadedIds.has(conversation.id)),
              ...loaded,
            ];
          });
          setError("");
        }
      })
      .catch((caught) => {
        if (active) {
          setError(caught instanceof Error ? caught.message : "Could not load conversations.");
        }
      });
    return () => { active = false; };
  }, [ready, signedIn]);

  const value = useMemo<ConversationContextValue>(() => ({
    conversations,
    activeConversationId,
    draftVersion,
    setActiveConversationId,
    startNewChat,
    createConversation,
    deleteConversation,
    refreshConversations,
    error,
    clearError,
  }), [
    activeConversationId,
    clearError,
    conversations,
    createConversation,
    deleteConversation,
    draftVersion,
    error,
    refreshConversations,
    startNewChat,
  ]);

  return <ConversationContext.Provider value={value}>{children}</ConversationContext.Provider>;
}

export function useConversations() {
  const context = useContext(ConversationContext);
  if (context === null) {
    throw new Error("useConversations must be used within a ConversationProvider.");
  }
  return context;
}
