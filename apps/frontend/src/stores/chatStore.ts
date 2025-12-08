import { create } from 'zustand';
import type { Message } from '@/types/chat';

interface ChatState {
  activeConversationId: string | null;
  messages: Message[];
  isLoading: boolean;

  // Actions
  setActiveConversation: (conversationId: string | null) => void;
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  clearMessages: () => void;
  setLoading: (isLoading: boolean) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  activeConversationId: null,
  messages: [],
  isLoading: false,

  setActiveConversation: (conversationId) =>
    set({ activeConversationId: conversationId }),

  setMessages: (messages) => set({ messages }),

  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),

  clearMessages: () => set({ messages: [] }),

  setLoading: (isLoading) => set({ isLoading }),
}));
