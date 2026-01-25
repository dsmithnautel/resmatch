"use client";

import { useState, useCallback } from "react";
import { Upload, FileText, X, Loader2, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  onFilesSelect?: (files: File[]) => void;
  isLoading?: boolean;
  accept?: string;
  multiple?: boolean;
}

export function FileUpload({
  onFileSelect,
  onFilesSelect,
  isLoading = false,
  accept = ".pdf",
  multiple = true,
}: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const addFiles = useCallback(
    (newFiles: File[]) => {
      const pdfFiles = newFiles.filter((f) => f.type === "application/pdf");
      if (pdfFiles.length === 0) return;

      const updatedFiles = [...selectedFiles, ...pdfFiles];
      setSelectedFiles(updatedFiles);

      // Call both callbacks for compatibility
      if (onFilesSelect) {
        onFilesSelect(updatedFiles);
      }
      // Also call single file callback with first new file for backwards compat
      if (pdfFiles.length > 0) {
        onFileSelect(pdfFiles[0]);
      }
    },
    [selectedFiles, onFileSelect, onFilesSelect]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        const files = Array.from(e.dataTransfer.files);
        addFiles(files);
      }
    },
    [addFiles]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      e.preventDefault();
      if (e.target.files && e.target.files.length > 0) {
        const files = Array.from(e.target.files);
        addFiles(files);
      }
      // Reset input so same file can be selected again
      e.target.value = "";
    },
    [addFiles]
  );

  const removeFile = useCallback(
    (index: number) => {
      const updatedFiles = selectedFiles.filter((_, i) => i !== index);
      setSelectedFiles(updatedFiles);
      if (onFilesSelect) {
        onFilesSelect(updatedFiles);
      }
    },
    [selectedFiles, onFilesSelect]
  );

  const clearAllFiles = useCallback(() => {
    setSelectedFiles([]);
    if (onFilesSelect) {
      onFilesSelect([]);
    }
  }, [onFilesSelect]);

  return (
    <div className="w-full space-y-4">
      {/* Drop zone - always visible to allow adding more files */}
      <label
        htmlFor="file-upload"
        className={cn(
          "flex flex-col items-center justify-center w-full border-2 border-dashed rounded-lg cursor-pointer transition-colors",
          selectedFiles.length > 0 ? "h-32" : "h-64",
          dragActive
            ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
            : "border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800"
        )}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <div className="flex flex-col items-center justify-center py-4">
          {selectedFiles.length > 0 ? (
            <>
              <Plus className="w-6 h-6 mb-2 text-gray-400" />
              <p className="text-sm text-gray-500 dark:text-gray-400">
                <span className="font-semibold">Add more PDFs</span>
              </p>
            </>
          ) : (
            <>
              <Upload className="w-10 h-10 mb-3 text-gray-400" />
              <p className="mb-2 text-sm text-gray-500 dark:text-gray-400">
                <span className="font-semibold">Click to upload</span> or drag and
                drop
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                PDF files only (multiple allowed)
              </p>
            </>
          )}
        </div>
        <input
          id="file-upload"
          type="file"
          className="hidden"
          accept={accept}
          onChange={handleChange}
          disabled={isLoading}
          multiple={multiple}
        />
      </label>

      {/* Selected files list */}
      {selectedFiles.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {selectedFiles.length} file{selectedFiles.length !== 1 ? "s" : ""} selected
            </p>
            {selectedFiles.length > 1 && !isLoading && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearAllFiles}
                className="text-xs text-gray-500 hover:text-red-500"
              >
                Clear all
              </Button>
            )}
          </div>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {selectedFiles.map((file, index) => (
              <div
                key={`${file.name}-${index}`}
                className="flex items-center justify-between p-3 border rounded-lg bg-gray-50 dark:bg-gray-800"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <FileText className="w-6 h-6 text-blue-500 flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="font-medium text-gray-900 dark:text-white truncate">
                      {file.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {(file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                </div>
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin text-blue-500 flex-shrink-0" />
                ) : (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => removeFile(index)}
                    className="text-gray-500 hover:text-red-500 flex-shrink-0 h-8 w-8"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
