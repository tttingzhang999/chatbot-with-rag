import { api } from '@/lib/api';
import { API_ENDPOINTS } from '@/lib/apiEndpoints';
import type { ChunkListResponse } from '@/types/embed';

/**
 * Get all chunks for a document (read-only)
 */
export const getDocumentChunks = async (documentId: string): Promise<ChunkListResponse> => {
  const response = await api.get<ChunkListResponse>(
    API_ENDPOINTS.EMBED_DOCUMENT_CHUNKS(documentId)
  );
  return response.data;
};
