import { useEffect } from 'react';
import { useChatStore } from '@/stores/chatStore';
import { useConversations, useSendMessage, useConversationHistory } from '@/hooks/useChat';
import { MessageList } from '@/components/chat/MessageList';
import { ChatInput } from '@/components/chat/ChatInput';
import { ConversationSidebar } from '@/components/chat/ConversationSidebar';
import { toast } from 'sonner';

export const ChatPage = () => {
  const {
    activeConversationId,
    messages,
    setActiveConversation,
    clearMessages,
    isLoading: chatLoading,
  } = useChatStore();

  const { data: conversationsData, isLoading: conversationsLoading, refetch: refetchConversations } = useConversations();
  const { mutate: sendMessage } = useSendMessage();
  const { refetch: refetchHistory } = useConversationHistory(activeConversationId);

  // Initialize with a new conversation on mount
  useEffect(() => {
    setActiveConversation(null);
    clearMessages();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (activeConversationId) {
      refetchHistory();
    }
  }, [activeConversationId, refetchHistory]);

  const handleSendMessage = (message: string) => {
    if (!message.trim()) return;

    sendMessage({
      message,
      conversation_id: activeConversationId || undefined,
    });
  };

  const handleSelectConversation = (conversationId: string) => {
    setActiveConversation(conversationId);
  };

  const handleNewConversation = () => {
    setActiveConversation(null);
    clearMessages();
  };

  const handleDeleteConversation = (_conversationId: string) => {
    // TODO: Implement delete conversation API call
    toast.info('Delete conversation feature will be implemented in Phase 4');
  };

  const handleRefreshConversations = () => {
    refetchConversations();
    toast.success('Conversations refreshed');
  };

  return (
    <div className="flex h-full w-full">
      <ConversationSidebar
        conversations={conversationsData?.conversations || []}
        activeConversationId={activeConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onDeleteConversation={handleDeleteConversation}
        onRefresh={handleRefreshConversations}
        isRefreshing={conversationsLoading}
      />

      <div className="flex-1 flex flex-col min-h-0">
        <div className="flex-1 overflow-hidden">
          <MessageList messages={messages} isLoading={chatLoading} />
        </div>
        <div className="flex-shrink-0">
          <ChatInput onSendMessage={handleSendMessage} disabled={chatLoading} />
        </div>
      </div>
    </div>
  );
};
