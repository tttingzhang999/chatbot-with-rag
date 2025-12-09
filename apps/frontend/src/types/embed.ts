export interface ChunkListItem {
  id: string;
  document_id: string;
  chunk_index: number;
  content: string;
  created_at: string;
  metadata: Record<string, unknown>;
  embedding_dimension: number | null;
}

export interface ChunkListResponse {
  chunks: ChunkListItem[];
  total: number;
  document_id: string;
  document_name: string;
}
