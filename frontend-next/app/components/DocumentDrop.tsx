'use client';
import { useState } from 'react';
import { UploadCloud, BookOpen } from 'lucide-react';

export function DocumentDrop({ onIngest, loading = false }: { onIngest: (file: File) => void; loading?: boolean }) {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file && file.type === 'application/pdf') {
      onIngest(file);
    } else {
      alert('Please upload standard PDF files only.');
    }
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`border-2 border-dashed rounded-xl p-10 text-center transition-all duration-300 flex flex-col items-center justify-center gap-3 bg-[#0d1527]/40 ${
        isDragOver 
          ? 'border-[#00f5d4] bg-[#00f5d4]/5 scale-[1.01]' 
          : 'border-[#2e374a] hover:border-[#00f5d4]/50'
      }`}
    >
      {isDragOver ? (
        <UploadCloud className="h-12 w-12 text-[#00f5d4] animate-bounce" />
      ) : (
        <BookOpen className="h-12 w-12 text-[#64748b]" />
      )}
      <div>
        <p className="text-sm font-semibold text-white">Drop dynamic PDF manual here</p>
        <p className="text-xs text-[#64748b] mt-1">Upload mid-demo to observe knowledge graph self-healing live</p>
      </div>
    </div>
  );
}
