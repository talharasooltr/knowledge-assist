import { ChatWorkspace } from "@/features/chat/chat-workspace";

type ConversationPageProps = {
  params: Promise<{ conversationId: string }>;
};

export default async function ConversationPage({ params }: ConversationPageProps) {
  const { conversationId } = await params;
  return <ChatWorkspace conversationId={conversationId} key={conversationId} />;
}
