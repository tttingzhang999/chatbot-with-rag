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

  // Embed
  EMBED_DOCUMENT_CHUNKS: (documentId: string) => `/embeds/documents/${documentId}/chunks`,
  EMBED_CHUNK_BY_ID: (chunkId: string) => `/embeds/chunks/${chunkId}`,
  EMBED_RE_EMBED_CHUNK: (chunkId: string) => `/embeds/chunks/${chunkId}/re-embed`,
  EMBED_RE_EMBED_ALL: (documentId: string) => `/embeds/documents/${documentId}/re-embed-all`,
  EMBED_CONFIG: '/embeds/config',
} as const;
