import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  fetchDocuments,
  uploadDocument,
  deleteDocument,
} from '@/services/uploadService';
import type { Document, UploadProgress } from '@/types/document';
import { useState } from 'react';

/**
 * Fetch documents with smart polling
 * - Polls every 5 seconds if any document is pending/processing
 * - Pauses polling when tab is inactive
 */
export function useDocuments(profileId?: string) {
  const query = useQuery<Document[]>({
    queryKey: ['documents', profileId],
    queryFn: () => fetchDocuments(profileId),
    // Smart polling: only poll if there are pending/processing documents
    refetchInterval: (data) => {
      if (!data || !Array.isArray(data)) return false;
      const hasProcessingDocs = data.some(
        (doc) => doc.status === 'pending' || doc.status === 'processing'
      );
      return hasProcessingDocs ? 5000 : false; // Poll every 5s if needed
    },
    refetchIntervalInBackground: false, // Pause when tab inactive
  });

  const { data, isLoading, error, refetch, isRefetching } = query;

  return {
    documents: data ?? [],
    isLoading,
    error,
    refetch,
    isRefetching,
  };
}

/**
 * Upload document mutation with progress tracking
 */
export function useUploadDocument(profileId?: string) {
  const queryClient = useQueryClient();
  const [uploadProgress, setUploadProgress] = useState<Record<string, UploadProgress>>({});

  const mutation = useMutation({
    mutationFn: async (file: File) => {
      const tempId = `temp-${Date.now()}-${file.name}`;

      // Initialize progress state
      setUploadProgress((prev) => ({
        ...prev,
        [tempId]: {
          document_id: tempId,
          filename: file.name,
          progress: 0,
          status: 'uploading',
        },
      }));

      try {
        const documentId = await uploadDocument(file, profileId, (progress) => {
          setUploadProgress((prev) => ({
            ...prev,
            [tempId]: {
              ...prev[tempId],
              progress,
            },
          }));
        });

        // Update to processing status
        setUploadProgress((prev) => ({
          ...prev,
          [tempId]: {
            ...prev[tempId],
            document_id: documentId,
            progress: 100,
            status: 'processing',
          },
        }));

        return documentId;
      } catch (error) {
        setUploadProgress((prev) => ({
          ...prev,
          [tempId]: {
            ...prev[tempId],
            status: 'failed',
            error: error instanceof Error ? error.message : 'Upload failed',
          },
        }));
        throw error;
      }
    },
    onSuccess: () => {
      // Refetch documents list
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      toast.success('Document uploaded successfully');
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Failed to upload document');
    },
  });

  // Clean up completed/failed uploads from progress state
  const clearProgress = (tempId: string) => {
    setUploadProgress((prev) => {
      const { [tempId]: _, ...rest } = prev;
      return rest;
    });
  };

  return {
    ...mutation,
    uploadProgress,
    clearProgress,
  };
}

/**
 * Delete document mutation
 */
export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      toast.success('Document deleted successfully');
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Failed to delete document');
    },
  });
}

/**
 * Upload multiple documents in parallel
 */
export function useUploadMultipleDocuments(profileId?: string) {
  const { mutateAsync: uploadDocument } = useUploadDocument(profileId);
  const { documents } = useDocuments();
  const [uploadProgress, setUploadProgress] = useState<Record<string, UploadProgress>>({});

  const uploadMultiple = async (files: File[]) => {
    // Check for duplicate file names
    const existingFileNames = new Set(documents.map((doc) => doc.file_name.toLowerCase()));
    const duplicateFiles: string[] = [];
    const filesToUpload = files.filter((file) => {
      const fileName = file.name.toLowerCase();
      if (existingFileNames.has(fileName)) {
        duplicateFiles.push(file.name);
        return false;
      }
      return true;
    });

    // Show warning if there are duplicate files
    if (duplicateFiles.length > 0) {
      toast.warning(
        `Skipped ${duplicateFiles.length} duplicate file(s): ${duplicateFiles.join(', ')}`
      );
    }

    // If no files to upload after filtering, return early
    if (filesToUpload.length === 0) {
      return files.map((file) => ({
        success: false,
        error: 'File already exists',
        filename: file.name,
      }));
    }

    const uploads = filesToUpload.map((file) => {
      const tempId = `temp-${Date.now()}-${file.name}`;

      setUploadProgress((prev) => ({
        ...prev,
        [tempId]: {
          document_id: tempId,
          filename: file.name,
          progress: 0,
          status: 'uploading',
        },
      }));

      return uploadDocument(file)
        .then((documentId) => {
          setUploadProgress((prev) => ({
            ...prev,
            [tempId]: {
              ...prev[tempId],
              document_id: documentId,
              progress: 100,
              status: 'completed',
            },
          }));
          return { success: true, documentId, filename: file.name };
        })
        .catch((error) => {
          setUploadProgress((prev) => ({
            ...prev,
            [tempId]: {
              ...prev[tempId],
              status: 'failed',
              error: error instanceof Error ? error.message : 'Upload failed',
            },
          }));
          return { success: false, error, filename: file.name };
        });
    });

    const results = await Promise.all(uploads);

    const successCount = results.filter((r) => r.success).length;
    const failCount = results.filter((r) => !r.success).length;

    if (successCount > 0) {
      toast.success(`${successCount} document(s) uploaded successfully`);
    }
    if (failCount > 0) {
      toast.error(`${failCount} document(s) failed to upload`);
    }

    return results;
  };

  return {
    uploadMultiple,
    uploadProgress,
  };
}
