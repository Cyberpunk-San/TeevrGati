"use client";

import React, { useState } from "react";
import { BookOpen, Layers, CheckCircle, AlertTriangle, Loader2 } from "lucide-react";
import { apiPost, ApiError } from "../lib/apiClient";
import { DocumentDrop } from "../components/DocumentDrop";

export default function IngestPage() {
  const [uploadStatus, setUploadStatus] = useState<"idle" | "uploading" | "success" | "error">("idle");
  const [uploadStats, setUploadStats] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleIngest = async (file: File) => {
    setLoading(true);
    setError(null);
    setUploadStatus("uploading");
    setUploadStats(null);

    const reader = new FileReader();
    reader.onload = async () => {
      if (typeof reader.result !== "string") return;
      const base64Content = reader.result.split(",")[1];
      try {
        const stats = await apiPost<Record<string, unknown>>("/api/ingest", {
          filename: file.name,
          content: base64Content,
        });
        setUploadStats(stats);
        setUploadStatus("success");
      } catch (err) {
        const msg = err instanceof ApiError ? err.detail : "Upload failed — check backend logs.";
        setError(msg);
        setUploadStatus("error");
      } finally {
        setLoading(false);
      }
    };
    reader.readAsDataURL(file);
  };

  const handleError = (msg: string) => {
    setError(msg);
    setUploadStatus("error");
  };

  return (
    <div className="page-shell">
      <div className="page-header">
        <div>
          <div className="label">Knowledge base</div>
          <h1 className="page-title" style={{ marginTop: 8 }}>Ingest SOP &amp; manuals</h1>
          <p className="page-subtitle">
            Drop a PDF or image to update the RAG index and knowledge graph without a full rebuild.
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

      {/* Error banner */}
      {error && (
        <div style={{
          padding: "14px 18px", borderRadius: "var(--r-sm)",
          background: "rgba(244,63,94,0.08)", border: "1px solid rgba(244,63,94,0.3)",
          color: "var(--danger)", fontSize: 13, display: "flex", alignItems: "center", gap: 10,
        }}>
          <AlertTriangle size={15} style={{ flexShrink: 0 }} />
          {error}
          <button
            onClick={() => setError(null)}
            style={{ marginLeft: "auto", background: "none", border: "none", cursor: "pointer", color: "inherit" }}
          >✕</button>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 28, alignItems: "start" }}>

        {/* Upload card */}
        <div className="card card-pad" style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div className="label" style={{ color: "var(--accent)" }}>PDF / image upload</div>

          <DocumentDrop onIngest={handleIngest} onError={handleError} loading={loading} />

          {/* Status indicator */}
          {uploadStatus !== "idle" && (
            <div style={{
              padding: "14px 16px",
              borderRadius: "var(--r-sm)",
              background: "var(--bg-base)",
              border: `1px solid ${uploadStatus === "success" ? "rgba(16,185,129,0.3)" : uploadStatus === "error" ? "rgba(244,63,94,0.3)" : "var(--border)"}`,
              display: "flex", alignItems: "center", gap: 10, fontSize: 13,
            }}>
              {uploadStatus === "uploading" && <Loader2 size={14} color="var(--accent)" style={{ animation: "spin 1s linear infinite" }} />}
              {uploadStatus === "success"   && <CheckCircle size={14} color="var(--success)" />}
              {uploadStatus === "error"     && <AlertTriangle size={14} color="var(--danger)" />}
              <span style={{ color: uploadStatus === "success" ? "var(--success)" : uploadStatus === "error" ? "var(--danger)" : "var(--text-secondary)" }}>
                {uploadStatus === "uploading" ? "Uploading & executing parse chain…"
                  : uploadStatus === "success" ? "Indexed successfully"
                  : "Ingestion failed"}
              </span>
            </div>
          )}
        </div>

        {/* Schema card */}
        <div className="card card-pad">
          <div className="label" style={{ color: "var(--accent)", display: "flex", alignItems: "center", gap: 8, marginBottom: 20 }}>
            <Layers size={14} color="var(--accent)" />
            Document schema
          </div>

          {uploadStats ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <div style={{
                  padding: "14px 16px", borderRadius: "var(--r-sm)",
                  background: "var(--bg-base)", border: "1px solid var(--border-dim)",
                }}>
                  <div className="label" style={{ marginBottom: 6 }}>Total pages</div>
                  <div style={{ fontSize: 22, fontWeight: 560, letterSpacing: "-0.03em" }}>
                    {Array.isArray(uploadStats.pages) ? uploadStats.pages.length : 1}
                  </div>
                </div>
                <div style={{
                  padding: "14px 16px", borderRadius: "var(--r-sm)",
                  background: "var(--bg-base)", border: "1px solid var(--border-dim)",
                }}>
                  <div className="label" style={{ marginBottom: 6 }}>Engine</div>
                  <div style={{ fontSize: 12, fontFamily: "var(--font-mono)", color: "var(--text-secondary)", paddingTop: 4 }}>
                    Clean Text Parser
                  </div>
                </div>
              </div>

              {Array.isArray(uploadStats.parse_chain) && (
                <div style={{ borderTop: "1px solid var(--border-dim)", paddingTop: 16 }}>
                  <div className="label" style={{ marginBottom: 10 }}>Ingestion chain provenance</div>
                  <div style={{
                    padding: "12px 14px", borderRadius: "var(--r-sm)",
                    background: "var(--bg-base)", border: "1px solid var(--border-dim)",
                    display: "flex", flexDirection: "column", gap: 6,
                  }}>
                    {(uploadStats.parse_chain as string[]).map((c, idx) => (
                      <div key={idx} className="mono" style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--text-secondary)" }}>
                        <span style={{ color: "var(--accent)" }}>►</span>
                        {c}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div style={{
              border: "1px dashed var(--border)",
              borderRadius: "var(--r-md)",
              padding: 32, textAlign: "center",
              color: "var(--text-muted)", fontSize: 13, lineHeight: 1.6,
              minHeight: 200, display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              Upload a document to inspect metadata output
            </div>
          )}
        </div>

      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
