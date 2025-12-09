export interface PromptProfile {
  id: string;
  name: string;
  description: string | null;
  is_default: boolean;
  system_prompt: string;
  rag_system_prompt_template: string;
  chunk_size: number;
  chunk_overlap: number;
  top_k_chunks: number;
  semantic_search_ratio: number;
  relevance_threshold: number;
  llm_model_id: string;
  llm_temperature: number;
  llm_top_p: number;
  llm_max_tokens: number;
  created_at: string;
  updated_at: string;
}

export interface ProfileSummary {
  id: string;
  name: string;
  description: string | null;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProfileCreateRequest {
  name: string;
  description?: string | null;
  system_prompt: string;
  rag_system_prompt_template: string;
  chunk_size?: number;
  chunk_overlap?: number;
  top_k_chunks?: number;
  semantic_search_ratio?: number;
  relevance_threshold?: number;
  llm_model_id?: string;
  llm_temperature?: number;
  llm_top_p?: number;
  llm_max_tokens?: number;
}

export interface ProfileUpdateRequest {
  name?: string;
  description?: string | null;
  system_prompt?: string;
  rag_system_prompt_template?: string;
  chunk_size?: number;
  chunk_overlap?: number;
  top_k_chunks?: number;
  semantic_search_ratio?: number;
  relevance_threshold?: number;
  llm_model_id?: string;
  llm_temperature?: number;
  llm_top_p?: number;
  llm_max_tokens?: number;
}
