import { useState } from 'react';
import { Upload } from 'lucide-react';
import { UploadZone } from '@/components/documents/UploadZone';
import { DocumentList } from '@/components/documents/DocumentList';
import { useUploadMultipleDocuments } from '@/hooks/useDocuments';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';

export function DocumentsPage() {
  const { uploadMultiple, uploadProgress } = useUploadMultipleDocuments();
  const [isUploading, setIsUploading] = useState(false);

  const handleFilesSelected = async (files: File[]) => {
    setIsUploading(true);
    try {
      await uploadMultiple(files);
    } finally {
      setIsUploading(false);
    }
  };

  const activeUploads = Object.values(uploadProgress);

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="flex-shrink-0 px-6 py-6 space-y-6">
        {/* Header */}
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight">Documents</h1>
          <p className="text-muted-foreground">
            Upload and manage documents for RAG-powered conversations
          </p>
        </div>

        <Separator />

        {/* Upload section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5" />
              Upload Documents
            </CardTitle>
            <CardDescription>
              Upload PDF, DOCX, DOC, or TXT files. Documents will be automatically processed and indexed for intelligent search.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <UploadZone onFilesSelected={handleFilesSelected} disabled={isUploading} />

            {/* Upload progress */}
            {activeUploads.length > 0 && (
              <div className="mt-6 space-y-4">
                <h3 className="text-sm font-medium">Upload Progress</h3>
                <div className="space-y-3">
                  {activeUploads.map((upload) => (
                    <div key={upload.document_id} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium truncate flex-1 mr-4">
                          {upload.filename}
                        </span>
                        <span className="text-muted-foreground">
                          {upload.status === 'uploading' && `${upload.progress}%`}
                          {upload.status === 'processing' && 'Processing...'}
                          {upload.status === 'completed' && 'Completed'}
                          {upload.status === 'failed' && 'Failed'}
                        </span>
                      </div>
                      <Progress
                        value={upload.progress}
                        className={
                          upload.status === 'failed'
                            ? 'bg-destructive/20 [&>div]:bg-destructive'
                            : upload.status === 'completed'
                            ? 'bg-green-500/20 [&>div]:bg-green-500'
                            : ''
                        }
                      />
                      {upload.error && (
                        <p className="text-xs text-destructive">{upload.error}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Documents list */}
      <div className="flex-1 min-h-0 px-6 pb-6">
        <Card className="h-full flex flex-col">
          <CardHeader className="flex-shrink-0">
            <CardTitle>Your Documents</CardTitle>
            <CardDescription>
              Manage your uploaded documents. Documents are automatically processed for hybrid search (semantic + BM25).
            </CardDescription>
          </CardHeader>
          <CardContent className="flex-1 min-h-0 overflow-hidden">
            <ScrollArea className="h-full pr-4">
              <DocumentList />
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
