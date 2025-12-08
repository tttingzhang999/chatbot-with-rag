import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, AlertCircle } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface UploadZoneProps {
  onFilesSelected: (files: File[]) => void;
  disabled?: boolean;
}

const ACCEPTED_FILE_TYPES = {
  'application/pdf': ['.pdf'],
  'text/plain': ['.txt'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/msword': ['.doc'],
};

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

export function UploadZone({ onFilesSelected, disabled = false }: UploadZoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onFilesSelected(acceptedFiles);
      }
    },
    [onFilesSelected]
  );

  const {
    getRootProps,
    getInputProps,
    isDragActive,
    isDragReject,
    fileRejections,
  } = useDropzone({
    onDrop,
    accept: ACCEPTED_FILE_TYPES,
    maxSize: MAX_FILE_SIZE,
    multiple: true,
    disabled,
  });

  const hasErrors = fileRejections.length > 0;

  return (
    <div>
      <Card
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed p-8 text-center cursor-pointer transition-colors',
          'hover:border-primary hover:bg-accent/50',
          isDragActive && 'border-primary bg-accent',
          isDragReject && 'border-destructive bg-destructive/10',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
      >
        <input {...getInputProps()} />

        <div className="flex flex-col items-center justify-center gap-3">
          <div className={cn(
            'p-3 rounded-full',
            isDragActive && !isDragReject && 'bg-primary/10',
            isDragReject && 'bg-destructive/10'
          )}>
            {isDragReject ? (
              <AlertCircle className="h-8 w-8 text-destructive" />
            ) : (
              <Upload className={cn(
                'h-8 w-8',
                isDragActive ? 'text-primary' : 'text-muted-foreground'
              )} />
            )}
          </div>

          <div className="space-y-1">
            <p className="text-sm font-medium">
              {isDragActive
                ? isDragReject
                  ? 'Some files are not supported'
                  : 'Drop files here...'
                : 'Drag and drop files here, or click to browse'}
            </p>
            <p className="text-xs text-muted-foreground">
              Supports PDF, DOCX, DOC, TXT (max 50MB per file)
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <FileText className="h-4 w-4" />
            <span>Multiple files supported</span>
          </div>
        </div>
      </Card>

      {/* Error messages */}
      {hasErrors && (
        <div className="mt-3 space-y-1">
          {fileRejections.map(({ file, errors }) => (
            <div
              key={file.name}
              className="flex items-start gap-2 text-sm text-destructive"
            >
              <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium">{file.name}</p>
                <ul className="text-xs space-y-0.5 mt-1">
                  {errors.map((error) => (
                    <li key={error.code}>
                      {error.code === 'file-too-large'
                        ? 'File is larger than 50MB'
                        : error.code === 'file-invalid-type'
                        ? 'File type not supported'
                        : error.message}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
