import { FileText } from 'lucide-react';
import { DocumentItem } from './DocumentItem';
import { useDocuments, useDeleteDocument } from '@/hooks/useDocuments';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';

export function DocumentList() {
  const { documents, isLoading, error } = useDocuments();
  const { mutate: deleteDocument, isPending: isDeleting, variables: deletingId } = useDeleteDocument();

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3 p-4 border rounded-lg">
            <Skeleton className="h-10 w-10 rounded" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-48" />
              <Skeleton className="h-3 w-32" />
            </div>
            <Skeleton className="h-6 w-16 rounded-full" />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Failed to load documents: {error instanceof Error ? error.message : 'Unknown error'}
        </AlertDescription>
      </Alert>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="p-4 rounded-full bg-muted mb-4">
          <FileText className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold mb-1">No documents yet</h3>
        <p className="text-sm text-muted-foreground max-w-sm">
          Upload your first document to get started. Documents will be processed and indexed for RAG-powered conversations.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {documents.length} document{documents.length !== 1 ? 's' : ''}
        </p>
      </div>

      <div className="space-y-2">
        {documents.map((document) => (
          <DocumentItem
            key={document.id}
            document={document}
            onDelete={deleteDocument}
            isDeleting={isDeleting && deletingId === document.id}
          />
        ))}
      </div>
    </div>
  );
}
