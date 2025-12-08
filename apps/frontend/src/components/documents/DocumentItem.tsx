import { FileText, Trash2, Clock, CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import type { Document } from '@/types/document';
import { cn } from '@/lib/utils';

interface DocumentItemProps {
  document: Document;
  onDelete?: (documentId: string) => void;
  isDeleting?: boolean;
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString();
}

const statusConfig = {
  pending: {
    icon: Clock,
    label: 'Pending',
    variant: 'secondary' as const,
    className: 'text-muted-foreground',
  },
  processing: {
    icon: Loader2,
    label: 'Processing',
    variant: 'default' as const,
    className: 'text-blue-500 animate-spin',
  },
  completed: {
    icon: CheckCircle2,
    label: 'Completed',
    variant: 'default' as const,
    className: 'text-green-500',
  },
  failed: {
    icon: XCircle,
    label: 'Failed',
    variant: 'destructive' as const,
    className: 'text-destructive',
  },
};

export function DocumentItem({ document, onDelete, isDeleting = false }: DocumentItemProps) {
  const status = statusConfig[document.status];
  const StatusIcon = status.icon;

  return (
    <Card className="hover:bg-accent/50 transition-colors">
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          {/* File icon */}
          <div className="p-2 rounded-lg bg-primary/10">
            <FileText className="h-5 w-5 text-primary" />
          </div>

          {/* File info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{document.filename}</p>
                <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                  <span>{formatFileSize(document.file_size)}</span>
                  <span>•</span>
                  <span>{formatDate(document.created_at)}</span>
                </div>
              </div>

              {/* Status badge */}
              <Badge
                variant={status.variant}
                className={cn('flex items-center gap-1.5 shrink-0')}
              >
                <StatusIcon className={cn('h-3 w-3', status.className)} />
                <span>{status.label}</span>
              </Badge>
            </div>

            {/* Error message */}
            {document.status === 'failed' && document.error_message && (
              <p className="mt-2 text-xs text-destructive">
                {document.error_message}
              </p>
            )}

            {/* Actions */}
            <div className="flex items-center gap-2 mt-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onDelete?.(document.id)}
                disabled={isDeleting}
                className="h-8 text-xs"
              >
                {isDeleting ? (
                  <>
                    <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 className="h-3 w-3 mr-1" />
                    Delete
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
