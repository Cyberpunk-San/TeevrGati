'use client';
import { useState } from 'react';
import { UploadCloud, BookOpen } from 'lucide-react';

const ACCEPTED_MIME_TYPES = [
  'application/pdf',
  'image/png',
  'image/jpeg',
  'image/tiff',
  'image/bmp',
];

export function DocumentDrop({
  onIngest,
  onError,
  loading = false,
}: {
  onIngest: (file: File) => void;
  onError?: (msg: string) => void;
  loading?: boolean;
}) {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleFile = (file: File | undefined) => {
    if (!file) return;
    if (!ACCEPTED_MIME_TYPES.includes(file.type)) {
      onError?.('Unsupported file type. Please upload a PDF or image (PNG, JPG, TIFF, BMP).');
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      onError?.('File too large. Maximum upload size is 20 MB.');
      return;
    }
    onIngest(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => setIsDragOver(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    handleFile(e.dataTransfer.files?.[0]);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFile(e.target.files?.[0]);
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      style={{
        border: `2px dashed ${isDragOver ? 'var(--accent)' : 'var(--border)'}`,
        borderRadius: 'var(--r-md)',
        padding: '40px 24px',
        textAlign: 'center',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 12,
        background: isDragOver ? 'var(--accent-dim)' : 'var(--bg-base)',
        transition: 'border-color 0.2s ease, background 0.2s ease',
        position: 'relative',
        minHeight: 220,
        cursor: loading ? 'not-allowed' : 'pointer',
        opacity: loading ? 0.6 : 1,
      }}
    >
      <input
        type="file"
        accept="application/pdf,image/png,image/jpeg,image/tiff,image/bmp"
        onChange={handleChange}
        disabled={loading}
        style={{
          position: 'absolute',
          inset: 0,
          opacity: 0,
          cursor: loading ? 'not-allowed' : 'pointer',
          width: '100%',
          height: '100%',
        }}
      />
      {isDragOver ? (
        <UploadCloud size={40} color="var(--accent)" />
      ) : (
        <BookOpen size={40} color="var(--text-muted)" />
      )}
      <div>
        <p style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-primary)' }}>
          {loading ? 'Uploading…' : 'Drop a PDF or image here'}
        </p>
        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
          or <span style={{ color: 'var(--accent)' }}>browse files</span>
          {' '}— PDF, PNG, JPG, TIFF, BMP · max 20 MB
        </p>
      </div>
    </div>
  );
}
