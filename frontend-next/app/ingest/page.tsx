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
    <div className="flex-1 flex flex-col p-6 gap-6">
      
      {/* Page Header */}
      <div className="flex justify-between items-center bg-[#0d1527] border border-[#1e293b] p-6 rounded-xl shadow-lg">
        <div>
          <h2 className="text-xl font-bold text-white tracking-wide">SOP & MANUAL INGESTION PORTAL</h2>
          <p className="text-xs text-[#64748b]">Upload OEM spec guidelines and maintenance SOPs to build RAG vector contexts</p>
        </div>
        <div className="h-10 w-10 rounded-lg bg-[#00f5d4]/10 border border-[#00f5d4]/20 flex items-center justify-center">
          <BookOpen className="h-5.5 w-5.5 text-[#00f5d4]" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Upload Card Area (Left 7 columns) */}
        <div className="lg:col-span-7 bg-[#111827]/80 border border-[#1e293b] rounded-xl p-5 shadow-xl flex flex-col gap-4">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2 text-[#00f5d4]">
            📥 OEM PDF Upload
          </h3>

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

        {/* Stats Inspector Panel (Right 5 columns) */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          <div className="bg-[#111827]/80 border border-[#1e293b] rounded-xl p-5 shadow-xl flex-1">
            <h3 className="text-xs font-bold text-[#00f5d4] uppercase tracking-wider mb-4 flex items-center gap-2">
              <Layers className="h-4 w-4 text-[#00f5d4]" />
              Ingested Document Schema
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
    </div>
  );
}
