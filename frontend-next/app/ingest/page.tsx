"use client";

import React, { useState } from "react";
import { BookOpen, RefreshCw, Layers } from "lucide-react";

export default function IngestPage() {
  const [uploadStatus, setUploadStatus] = useState("");
  const [uploadStats, setUploadStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setUploadStatus("Uploading & executing parse chain...");
    setUploadStats(null);
    
    const reader = new FileReader();
    reader.onload = async () => {
      if (typeof reader.result !== "string") return;
      const base64Content = reader.result.split(",")[1];
      try {
        const res = await fetch("http://localhost:8000/api/ingest", {
          method: "POST",
          headers: { 
            "Content-Type": "application/json",
            "Authorization": "Bearer dev-key"
          },
          body: JSON.stringify({
            filename: file.name,
            content: base64Content
          })
        });
        if (res.ok) {
          const stats = await res.json();
          setUploadStats(stats);
          setUploadStatus("Success");
        } else {
          setUploadStatus("Parse Failed");
        }
      } catch (err) {
        setUploadStatus("Upload failed");
      } finally {
        setLoading(false);
      }
    };
    reader.readAsDataURL(file);
  };

  return (
    <div className="page-shell">
      <div className="page-header">
        <div>
          <div className="label">Knowledge base</div>
          <h1 className="page-title" style={{ marginTop: 8 }}>Ingest SOP & manuals</h1>
          <p className="page-subtitle">
            Drop a PDF to update the RAG index and knowledge graph without a full rebuild.
          </p>
        </div>
        <div style={{
          height: 44, width: 44, borderRadius: 12,
          background: "var(--accent-dim)", border: "1px solid rgba(34,211,238,0.2)",
          display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          <BookOpen size={18} color="var(--accent)" />
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 28, alignItems: "start" }}>
        <div className="card card-pad" style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <h3 className="label" style={{ color: "var(--accent)" }}>PDF upload</h3>

          <div className="border-2 border-dashed border-[#2e374a] rounded-lg p-12 flex flex-col items-center justify-center gap-4 hover:border-[#00f5d4] transition-all bg-[#0d1527]/50 relative min-h-[280px]">
            <input 
              type="file" 
              accept="application/pdf"
              onChange={handleFileUpload}
              className="absolute inset-0 opacity-0 cursor-pointer" 
            />
            {loading ? (
              <RefreshCw className="h-12 w-12 text-[#00f5d4] animate-spin" />
            ) : (
              <BookOpen className="h-12 w-12 text-[#94a3b8]" />
            )}
            <span className="text-sm text-[#94a3b8] text-center font-medium">
              Drag and drop manual PDF files or <span className="text-[#00f5d4] underline">Browse Files</span>
            </span>
            <span className="text-[10px] text-[#475569] text-center max-w-xs">
              Supports OEM operation instructions, historical incident records, and safety regulations
            </span>
          </div>

          {uploadStatus && (
            <div className="p-4 bg-[#0d1527] rounded-lg border border-[#2e374a] text-xs">
              <span className="text-[#64748b]">Parser Execution Status:</span>{" "}
              <span className={uploadStatus.includes("Success") ? "text-[#00f5d4] font-bold" : "text-[#f72585] font-bold"}>
                {uploadStatus.toUpperCase()}
              </span>
            </div>
          )}
        </div>

        <div className="card card-pad">
          <h3 className="label" style={{ color: "var(--accent)", display: "flex", alignItems: "center", gap: 8, marginBottom: 20 }}>
            <Layers size={14} color="var(--accent)" />
            Document schema
          </h3>

            {uploadStats ? (
              <div className="flex flex-col gap-4 text-xs">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-[#0d1527] p-3 rounded border border-[#1e293b]">
                    <span className="text-[#64748b] text-[10px] block">TOTAL PAGES</span>
                    <span className="text-white text-lg font-bold">{uploadStats.pages ? uploadStats.pages.length : 1}</span>
                  </div>
                  <div className="bg-[#0d1527] p-3 rounded border border-[#1e293b]">
                    <span className="text-[#64748b] text-[10px] block">EXTRACTION ENGINE</span>
                    <span className="text-white text-xs font-bold font-mono">Clean Text Parser</span>
                  </div>
                </div>

                {uploadStats.parse_chain && (
                  <div className="border-t border-[#1e293b] pt-4 mt-2">
                    <span className="text-[#64748b] text-[10px] block uppercase mb-2">Ingestion Chain Provenance</span>
                    <div className="flex flex-col gap-1.5 bg-[#0d1527] p-3 rounded border border-[#1e293b] font-mono text-[10px] text-slate-300">
                      {uploadStats.parse_chain.map((c: string, idx: number) => (
                        <div key={idx} className="flex items-center gap-2">
                          <span className="text-[#00f5d4]">►</span>
                          <span>{c}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center text-center h-48 border border-dashed border-[#2e374a] rounded-lg p-6">
                <span className="text-xs text-[#64748b]">Upload a PDF manual to inspect metadata output</span>
              </div>
            )}
        </div>

      </div>
    </div>
  );
}
