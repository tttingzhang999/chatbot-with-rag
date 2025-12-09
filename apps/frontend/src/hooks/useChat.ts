import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { chatService } from '@/services/chatService';
import { useChatStore } from '@/stores/chatStore';
import type { ChatRequest } from '@/types/chat';
import { toast } from 'sonner';

export const useConversations = (profileId?: string) => {
  return useQuery({
    queryKey: ['conversations', profileId],
    queryFn: () => chatService.getConversations(profileId),
  });
};

export const useConversationHistory = (conversationId: string | null) => {
  const { setMessages } = useChatStore();

  return useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: async () => {
      const data = await chatService.getConversationHistory(conversationId!);
      setMessages(data.messages);
      return data;
    },
    enabled: !!conversationId,
  });
};

export const useSendMessage = () => {
  const queryClient = useQueryClient();
  const { addMessage, setLoading, setActiveConversation } = useChatStore();

  return useMutation({
    mutationFn: (data: ChatRequest) => chatService.sendMessage(data),
    onMutate: async (variables) => {
      // Immediately add user message to UI
      const tempUserMessage = {
        id: `temp-${Date.now()}`,
        conversation_id: variables.conversation_id || '',
        content: variables.message,
        role: 'user' as const,
        created_at: new Date().toISOString(),
      };
      addMessage(tempUserMessage);
      setLoading(true);
    },
    onSuccess: (data) => {
      // Only add assistant response (user message already added in onMutate)
      const assistantMessage = data.messages.find((msg) => msg.role === 'assistant');
      if (assistantMessage) {
        addMessage(assistantMessage);
      }

      // Update active conversation if it was a new conversation
      setActiveConversation(data.conversation_id);

      // Invalidate conversations list to update it
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      setLoading(false);
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || 'Failed to send message';
      toast.error(errorMessage);
      setLoading(false);
    },
  });
};

export const useCreateConversation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: chatService.createConversation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });
};

export const useDeleteConversation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (conversationId: string) => chatService.deleteConversation(conversationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      toast.success('Conversation deleted');
    },
    onError: () => {
      toast.error('Failed to delete conversation');
    },
  });
};
