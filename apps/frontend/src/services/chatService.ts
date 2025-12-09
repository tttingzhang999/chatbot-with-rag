import { api } from '@/lib/api';
import { API_ENDPOINTS } from '@/lib/apiEndpoints';
import type {
  ChatRequest,
  ChatResponse,
  ConversationListResponse,
  ConversationHistoryResponse
} from '@/types/chat';

export const chatService = {
  sendMessage: async (data: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>(
      API_ENDPOINTS.CHAT_MESSAGE,
      data
    );
    return response.data;
  },

  getConversations: async (profileId?: string): Promise<ConversationListResponse> => {
    const response = await api.get<ConversationListResponse>(
      API_ENDPOINTS.CHAT_CONVERSATIONS,
      { params: profileId ? { profile_id: profileId } : undefined }
    );
    return response.data;
  },

  getConversationHistory: async (conversationId: string): Promise<ConversationHistoryResponse> => {
    const response = await api.get<ConversationHistoryResponse>(
      API_ENDPOINTS.CHAT_CONVERSATION_BY_ID(conversationId)
    );
    return response.data;
  },

  createConversation: async (): Promise<{ conversation_id: string }> => {
    const response = await api.post<{ conversation_id: string }>(
      API_ENDPOINTS.CHAT_CONVERSATIONS
    );
    return response.data;
  },

  deleteConversation: async (conversationId: string): Promise<void> => {
    await api.delete(API_ENDPOINTS.CHAT_CONVERSATION_BY_ID(conversationId));
  },
};
