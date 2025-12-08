import axios from 'axios';
import { api } from '@/lib/api';
import type {
  PresignedUrlRequest,
  PresignedUrlResponse,
  ProcessDocumentRequest,
  Document,
} from '@/types/document';

/**
 * S3 Pre-signed URL Upload Flow:
 * 1. Request pre-signed URL from backend
 * 2. Upload file directly to S3 using the pre-signed URL
 * 3. Trigger document processing
 * 4. Poll document status via React Query
 */

/**
 * Step 1: Request pre-signed URL for S3 upload
 */
export async function requestPresignedUrl(
  data: PresignedUrlRequest
): Promise<PresignedUrlResponse> {
  const response = await api.post<PresignedUrlResponse>('/upload/presigned-url', data);
  return response.data;
}

/**
 * Step 2: Upload file directly to S3 using pre-signed URL
 * Note: This bypasses the API client to upload directly to S3
 */
export async function uploadToS3(
  uploadUrl: string,
  file: File,
  onProgress?: (progress: number) => void
): Promise<void> {
  await axios.put(uploadUrl, file, {
    headers: {
      'Content-Type': file.type,
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percentCompleted);
      }
    },
  });
}

/**
 * Step 3: Trigger document processing after S3 upload
 */
export async function processDocument(data: ProcessDocumentRequest): Promise<void> {
  await api.post('/upload/process-document', data);
}

/**
 * Fetch all documents for the current user
 */
export async function fetchDocuments(): Promise<Document[]> {
  const response = await api.get<{ documents: Document[]; total: number }>('/upload/documents');
  return response.data.documents;
}

/**
 * Delete a document
 */
export async function deleteDocument(documentId: string): Promise<void> {
  await api.delete(`/upload/documents/${documentId}`);
}

/**
 * Complete upload flow: Request URL -> Upload to S3 -> Trigger processing
 */
export async function uploadDocument(
  file: File,
  onProgress?: (progress: number) => void
): Promise<string> {
  // Extract file extension from filename
  const fileExtension = file.name.split('.').pop()?.toLowerCase() || '';

  // Step 1: Request pre-signed URL
  const { upload_url, document_id } = await requestPresignedUrl({
    filename: file.name,
    file_type: fileExtension,
    file_size: file.size,
  });

  // Step 2: Upload to S3
  await uploadToS3(upload_url, file, onProgress);

  // Step 3: Trigger processing
  await processDocument({ document_id });

  return document_id;
}
