"use client";

import { ChatWorkspace } from "@/features/chat/chat-workspace";
import { useConversations } from "@/features/chat/conversation-context";

export default function NewChatPage() {
  const { draftVersion } = useConversations();
  return <ChatWorkspace conversationId={null} key={draftVersion} />;
}
