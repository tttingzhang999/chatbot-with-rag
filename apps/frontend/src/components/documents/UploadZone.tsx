import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, AlertCircle } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

interface UploadZoneProps {
  onFilesSelected: (files: File[]) => void;
  disabled?: boolean;
  existingFileNames?: string[];
}

const ACCEPTED_FILE_TYPES = {
  'application/pdf': ['.pdf'],
  'text/plain': ['.txt'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/msword': ['.doc'],
};

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

export function UploadZone({
  onFilesSelected,
  disabled = false,
  existingFileNames = []
}: UploadZoneProps) {
  const [duplicateFiles, setDuplicateFiles] = useState<string[]>([]);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        // Check for duplicate file names
        const existingNamesSet = new Set(
          existingFileNames.map((name) => name.toLowerCase())
        );
        const duplicates: File[] = [];
        const validFiles: File[] = [];

        acceptedFiles.forEach((file) => {
          if (existingNamesSet.has(file.name.toLowerCase())) {
            duplicates.push(file);
          } else {
            validFiles.push(file);
          }
        });

        // Show warning for duplicate files
        if (duplicates.length > 0) {
          const duplicateNames = duplicates.map((f) => f.name);
          setDuplicateFiles(duplicateNames);
          toast.warning(
            `Skipped ${duplicates.length} duplicate file(s): ${duplicateNames.join(', ')}`
          );
          // Clear duplicate files after 5 seconds
          setTimeout(() => setDuplicateFiles([]), 5000);
        } else {
          setDuplicateFiles([]);
        }

        // Only pass valid files to the callback
        if (validFiles.length > 0) {
          onFilesSelected(validFiles);
        } else if (duplicates.length > 0) {
          // If all files are duplicates, show error
          toast.error('All selected files already exist. Please choose different files.');
        }
      }
    },
    [onFilesSelected, existingFileNames]
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
          'border-2 border-dashed p-4 text-center cursor-pointer transition-colors',
          'hover:border-primary hover:bg-accent/50',
          isDragActive && 'border-primary bg-accent',
          isDragReject && 'border-destructive bg-destructive/10',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
      >
        <input {...getInputProps()} />

        <div className="flex flex-col items-center justify-center gap-2">
          <div className={cn(
            'p-2 rounded-full',
            isDragActive && !isDragReject && 'bg-primary/10',
            isDragReject && 'bg-destructive/10'
          )}>
            {isDragReject ? (
              <AlertCircle className="h-5 w-5 text-destructive" />
            ) : (
              <Upload className={cn(
                'h-5 w-5',
                isDragActive ? 'text-primary' : 'text-muted-foreground'
              )} />
            )}
          </div>
          <div className="space-y-0.5">
            <p className="text-xs font-medium">
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
        </div>
      </Card>

      {/* Error messages */}
      {(hasErrors || duplicateFiles.length > 0) && (
        <div className="mt-3 space-y-1">
          {/* Duplicate file errors */}
          {duplicateFiles.map((fileName) => (
            <div
              key={fileName}
              className="flex items-start gap-2 text-sm text-destructive"
            >
              <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
              <div>
                <p className="font-medium">{fileName}</p>
                <p className="text-xs mt-1">File already exists</p>
              </div>
            </div>
          ))}
          {/* File rejection errors */}
          {fileRejections.map(({ file, errors }) => (
            <div
              key={file.name}
              className="flex items-start gap-2 text-sm text-destructive"
            >
              <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
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
