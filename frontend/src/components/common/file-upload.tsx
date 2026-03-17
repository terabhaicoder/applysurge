"use client";

import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, File, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface FileUploadProps {
  accept?: Record<string, string[]>;
  maxSize?: number;
  onDrop: (files: File[]) => void;
  currentFile?: string;
  onRemove?: () => void;
  label?: string;
  description?: string;
  className?: string;
}

export function FileUpload({
  accept = { "application/pdf": [".pdf"], "application/msword": [".doc", ".docx"] },
  maxSize = 10 * 1024 * 1024,
  onDrop,
  currentFile,
  onRemove,
  label = "Upload file",
  description = "PDF or DOC, max 10MB",
  className,
}: FileUploadProps) {
  const handleDrop = useCallback((acceptedFiles: File[]) => {
    onDrop(acceptedFiles);
  }, [onDrop]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleDrop,
    accept,
    maxSize,
    multiple: false,
  });

  if (currentFile) {
    return (
      <div className={cn("flex items-center gap-3 p-3 bg-secondary rounded-lg border border-border", className)}>
        <File className="w-8 h-8 text-blue-600" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-foreground truncate">{currentFile}</p>
          <p className="text-xs text-muted-foreground">Uploaded successfully</p>
        </div>
        {onRemove && (
          <button onClick={onRemove} className="p-1 hover:bg-border rounded">
            <X className="w-4 h-4 text-muted-foreground" />
          </button>
        )}
      </div>
    );
  }

  return (
    <div
      {...getRootProps()}
      className={cn(
        "border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors",
        isDragActive ? "border-blue-400 bg-blue-50" : "border-border hover:border-muted-foreground bg-secondary",
        className
      )}
    >
      <input {...getInputProps()} />
      <Upload className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
      <p className="text-sm font-medium text-foreground">{label}</p>
      <p className="text-xs text-muted-foreground mt-1">{description}</p>
    </div>
  );
}
