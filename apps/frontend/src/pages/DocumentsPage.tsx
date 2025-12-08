import { useState } from 'react';
import { Upload, RefreshCw } from 'lucide-react';
import { UploadZone } from '@/components/documents/UploadZone';
import { DocumentList } from '@/components/documents/DocumentList';
import { useUploadMultipleDocuments, useDocuments } from '@/hooks/useDocuments';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';

export function DocumentsPage() {
  const { uploadMultiple } = useUploadMultipleDocuments();
  const { refetch, isRefetching } = useDocuments();
  const [isUploading, setIsUploading] = useState(false);

  const handleFilesSelected = async (files: File[]) => {
    setIsUploading(true);
    try {
      await uploadMultiple(files);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="shrink-0 px-6 py-4 space-y-3">
        {/* Header with Upload section in horizontal layout */}
        <div className="flex items-center justify-between gap-6">
          {/* Left: Title and description */}
          <div className="space-y-0.5 shrink-0">
            <h1 className="text-2xl font-bold tracking-tight">Documents</h1>
            <p className="text-sm text-muted-foreground">
              Upload and manage documents for RAG-powered conversations
            </p>
          </div>

          {/* Right: Upload zone */}
          <Card className="w-100 shrink-0">
            <CardContent className="px-3 pb-3">
              <UploadZone onFilesSelected={handleFilesSelected} disabled={isUploading} />
            </CardContent>
          </Card>
        </div>

        <Separator />
      </div>

      {/* Documents list - takes most of the space */}
      <div className="flex-1 min-h-0 px-6 pb-6">
        <Card className="h-full flex flex-col">
          <CardHeader className="shrink-0 pb-3">
            <div className="flex items-start justify-between">
              <div>
                <CardTitle>Your Documents</CardTitle>
                <CardDescription>
                  Manage your uploaded documents. Documents are automatically processed for hybrid search (semantic + BM25).
                </CardDescription>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => refetch()}
                disabled={isRefetching}
                className="shrink-0"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${isRefetching ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </CardHeader>
          <CardContent className="flex-1 min-h-0 p-0">
            <ScrollArea className="h-full px-6">
              <DocumentList />
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
