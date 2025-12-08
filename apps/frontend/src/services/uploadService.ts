import axios from 'axios';
import { api } from '@/lib/api';
import type {
  PresignedUrlRequest,
  PresignedUrlResponse,
  ProcessDocumentRequest,
  Document,
  UploadConfig,
  LocalUploadResponse,
} from '@/types/document';

/**
 * Upload Modes:
 *
 * 1. S3 Pre-signed URL Upload Flow (USE_PRESIGNED_URLS=true):
 *    - Request pre-signed URL from backend
 *    - Upload file directly to S3 using the pre-signed URL
 *    - Trigger document processing
 *    - Poll document status via React Query
 *
 * 2. Local Storage Upload Flow (USE_PRESIGNED_URLS=false):
 *    - Upload file directly to backend
 *    - Backend saves to local storage and triggers processing
 *    - Poll document status via React Query
 */

/**
 * Get upload configuration from backend
 */
export async function getUploadConfig(): Promise<UploadConfig> {
  const response = await api.get<UploadConfig>('/upload/config');
  return response.data;
}

/**
 * Step 1: Request pre-signed URL for S3 upload (S3 mode only)
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
 * Upload file to local storage (Local mode only)
 */
export async function uploadToLocal(
  file: File,
  onProgress?: (progress: number) => void
): Promise<LocalUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post<LocalUploadResponse>('/upload/local', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percentCompleted);
      }
    },
  });

  return response.data;
}

/**
 * Step 3: Trigger document processing after S3 upload (S3 mode only)
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
 * Complete upload flow: Automatically detects mode and uses appropriate upload method
 *
 * This function:
 * 1. Fetches upload configuration from backend
 * 2. Uses S3 flow if USE_PRESIGNED_URLS=true
 * 3. Uses local upload flow if USE_PRESIGNED_URLS=false
 */
export async function uploadDocument(
  file: File,
  onProgress?: (progress: number) => void
): Promise<string> {
  // Get upload configuration from backend
  const config = await getUploadConfig();

  if (config.use_presigned_urls) {
    // S3 Pre-signed URL Upload Flow
    return await uploadDocumentViaS3(file, onProgress);
  } else {
    // Local Storage Upload Flow
    return await uploadDocumentViaLocal(file, onProgress);
  }
}

/**
 * S3 Upload Flow: Request URL -> Upload to S3 -> Trigger processing
 */
export async function uploadDocumentViaS3(
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

/**
 * Local Upload Flow: Upload to backend -> Backend processes immediately
 */
export async function uploadDocumentViaLocal(
  file: File,
  onProgress?: (progress: number) => void
): Promise<string> {
  // Upload to local storage (backend handles processing automatically)
  const response = await uploadToLocal(file, onProgress);
  return response.document_id;
}
