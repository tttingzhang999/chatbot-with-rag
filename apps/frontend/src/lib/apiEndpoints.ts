export const API_ENDPOINTS = {
  // Auth
  AUTH_REGISTER: '/auth/register',
  AUTH_LOGIN: '/auth/login',

  // Chat
  CHAT_MESSAGE: '/chat/message',
  CHAT_CONVERSATIONS: '/chat/conversations',
  CHAT_CONVERSATION_BY_ID: (id: string) => `/chat/conversations/${id}`,

  // Upload
  UPLOAD_PRESIGNED_URL: '/upload/presigned-url',
  UPLOAD_DOCUMENTS: '/upload/documents',
  UPLOAD_PROCESS_DOCUMENT: '/upload/process-document',
  UPLOAD_DOCUMENT_BY_ID: (id: string) => `/upload/documents/${id}`,

  // Profiles
  PROFILES: '/profiles',
  PROFILES_DEFAULT: '/profiles/default',
  PROFILE_BY_ID: (id: string) => `/profiles/${id}`,
  PROFILE_SET_DEFAULT: (id: string) => `/profiles/${id}/set-default`,
} as const;
