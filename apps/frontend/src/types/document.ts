export interface Document {
  id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  upload_date: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message: string | null;
  chunk_count: number;
}

export interface PresignedUrlRequest {
  filename: string;
  file_type: string;
  file_size: number;
}

export interface PresignedUrlResponse {
  upload_url: string;
  document_id: string;
  s3_key: string;
}

export interface ProcessDocumentRequest {
  document_id: string;
}

export interface UploadConfig {
  use_presigned_urls: boolean;
}

export interface LocalUploadResponse {
  document_id: string;
  status: string;
  message: string;
}

export interface UploadProgress {
  document_id: string;
  filename: string;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  error?: string;
}
