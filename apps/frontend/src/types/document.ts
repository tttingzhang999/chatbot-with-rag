export interface Document {
  id: string;
  user_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  s3_key: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message?: string;
  created_at: string;
  updated_at: string;
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

export interface UploadProgress {
  document_id: string;
  filename: string;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  error?: string;
}
