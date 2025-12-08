export type Message = {
  id: string;
  conversation_id: string;
  content: string;
  role: 'user' | 'assistant';
  created_at: string;
}

export type Conversation = {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export type ChatRequest = {
  message: string;
  conversation_id?: string;
}

export type ChatResponse = {
  conversation_id: string;
  messages: Message[];
}

export type ConversationListResponse = {
  conversations: Conversation[];
}

export type ConversationHistoryResponse = {
  conversation_id: string;
  messages: Message[];
}
