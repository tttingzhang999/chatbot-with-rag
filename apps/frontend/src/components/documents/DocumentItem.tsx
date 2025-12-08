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
      <CardContent className="p-3">
        <div className="flex items-center gap-3">
          {/* File icon */}
          <div className="p-1.5 rounded-lg bg-primary/10 shrink-0">
            <FileText className="h-4 w-4 text-primary" />
          </div>

          {/* File name */}
          <div className="flex-1 min-w-0">
            <p className="font-medium truncate text-sm">{document.file_name}</p>
          </div>

          {/* Metadata */}
          <div className="flex items-center gap-2 text-xs text-muted-foreground shrink-0">
            <span>{formatFileSize(document.file_size)}</span>
            <span>•</span>
            <span>{formatDate(document.upload_date)}</span>
          </div>

          {/* Status badge */}
          <Badge
            variant={status.variant}
            className={cn('flex items-center gap-1 shrink-0 h-6')}
          >
            <StatusIcon className={cn('h-3 w-3', status.className)} />
            <span className="text-xs">{status.label}</span>
          </Badge>

          {/* Delete button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onDelete?.(document.id)}
            disabled={isDeleting}
            className="h-7 w-7 p-0 shrink-0"
            title="Delete document"
          >
            {isDeleting ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Trash2 className="h-3.5 w-3.5" />
            )}
          </Button>
        </div>

        {/* Error message (only shows on failed status) */}
        {document.status === 'failed' && document.error_message && (
          <p className="mt-2 text-xs text-destructive pl-9">
            {document.error_message}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
