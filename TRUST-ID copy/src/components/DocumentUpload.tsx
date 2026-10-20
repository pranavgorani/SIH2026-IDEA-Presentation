import React, { useRef, useState } from 'react';
import { UploadCloud, FileText, X, RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';
import { formatFileSize } from '../utils/formatters';

interface DocumentUploadProps {
  selectedFile: File | null;
  onFileSelect: (file: File | null) => void;
  documentType: string;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({
  selectedFile,
  onFileSelect,
  documentType,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  React.useEffect(() => {
    if (!selectedFile) {
      setPreviewUrl(null);
      return;
    }

    const objectUrl = URL.createObjectURL(selectedFile);
    setPreviewUrl(objectUrl);

    return () => URL.revokeObjectURL(objectUrl);
  }, [selectedFile]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.type.startsWith('image/') || file.type === 'application/pdf') {
        onFileSelect(file);
      }
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileSelect(e.target.files[0]);
    }
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onFileSelect(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleTriggerPicker = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="bg-white border border-[#dadce0] rounded-2xl p-5 shadow-xs relative font-sans">
      {/* Header section */}
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#f1f3f4]">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-full bg-[#e8f0fe] flex items-center justify-center text-[#1a73e8]">
            <FileText className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-[#202124]">
              Primary Document
            </h3>
            <p className="text-xs text-[#5f6368]">
              {documentType.replace(/_/g, ' ')} specimen
            </p>
          </div>
        </div>

        {selectedFile && (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-[#e6f4ea] text-[#137333] border border-[#ceead6]">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Ready</span>
          </span>
        )}
      </div>

      {/* Upload Dropzone or Image Preview */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,image/tiff,application/pdf"
        className="hidden"
        onChange={handleFileInputChange}
      />

      {!selectedFile ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleTriggerPicker}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-150 ${
            isDragging
              ? 'border-[#1a73e8] bg-[#e8f0fe]/40'
              : 'border-[#dadce0] hover:border-[#1a73e8] hover:bg-[#f8fafd] bg-[#fafbfc]'
          }`}
        >
          <div className="flex flex-col items-center justify-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-[#e8f0fe] flex items-center justify-center text-[#1a73e8]">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-[#202124]">
                Drag & drop document or <span className="text-[#1a73e8] underline">browse</span>
              </p>
              <p className="text-xs text-[#5f6368] mt-1">
                JPEG, PNG, WebP or PDF (up to 20MB)
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {/* Image Preview Window */}
          <div className="relative rounded-xl overflow-hidden border border-[#dadce0] bg-[#f8fafd] h-56 flex items-center justify-center group">
            {previewUrl && (
              <img
                src={previewUrl}
                alt="Document preview"
                className="max-h-full max-w-full object-contain"
              />
            )}

            {/* Quick Actions Hover Overlay */}
            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center space-x-2.5">
              <button
                type="button"
                onClick={handleTriggerPicker}
                className="px-3.5 py-1.5 rounded-full bg-white text-[#202124] hover:bg-[#f1f3f4] text-xs font-medium flex items-center space-x-1.5 shadow-sm"
              >
                <RefreshCw className="w-3.5 h-3.5 text-[#1a73e8]" />
                <span>Replace</span>
              </button>
              <button
                type="button"
                onClick={handleClear}
                className="px-3.5 py-1.5 rounded-full bg-[#d93025] text-white hover:bg-[#b31412] text-xs font-medium flex items-center space-x-1.5 shadow-sm"
              >
                <X className="w-3.5 h-3.5" />
                <span>Remove</span>
              </button>
            </div>
          </div>

          {/* Technical Metadata Bar */}
          <div className="bg-[#f8fafd] border border-[#e0e2e6] rounded-xl p-3 text-xs space-y-1">
            <div className="flex items-center justify-between text-[#202124]">
              <span className="text-[#5f6368]">File:</span>
              <span className="truncate max-w-[240px] font-medium">{selectedFile.name}</span>
            </div>
            <div className="flex items-center justify-between text-xs text-[#5f6368]">
              <span>Size:</span>
              <span>{formatFileSize(selectedFile.size)}</span>
            </div>
          </div>
        </div>
      )}

      {/* Advisory footer */}
      <div className="mt-3 flex items-center space-x-1.5 text-xs text-[#5f6368]">
        <AlertCircle className="w-3.5 h-3.5 text-[#5f6368] flex-shrink-0" />
        <span>Ensure all 4 corners and text fields are clearly visible without glare.</span>
      </div>
    </div>
  );
};
