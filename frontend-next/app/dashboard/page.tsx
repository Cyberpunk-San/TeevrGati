"use client";

import React, { useState, useEffect } from "react";
import { ShieldAlert, CheckCircle2, AlertTriangle, Play, RefreshCw } from "lucide-react";

interface ComplianceReport {
  docName: string;
  category: string;
  safetyScore: number;
  checks: {
    loto: boolean;
    grounding: boolean;
    ppe: boolean;
    ventilation: boolean;
  };
  gaps: string[];
}

const CHECK_LABELS: { key: keyof ComplianceReport["checks"]; label: string }[] = [
  { key: "loto", label: "LOTO" },
  { key: "ppe", label: "PPE" },
  { key: "grounding", label: "Grounding" },
  { key: "ventilation", label: "Gas testing" },
];

export default function Dashboard() {
  const [loading, setLoading] = useState(false);
  const [complianceData, setComplianceData] = useState<ComplianceReport[]>([
    {
      docName: "DOC_Pump_P-201_O&M_Manual.pdf",
      category: "Rotary equipment",
      safetyScore: 75,
      checks: { loto: true, grounding: false, ppe: true, ventilation: true },
      gaps: ["OISD-GDN-180: Electrostatic grounding bonding procedure omitted from maintenance routine."]
    },
    {
      docName: "SOP_Turbine_Bearing_Overhaul.pdf",
      category: "Safety procedure",
      safetyScore: 50,
      checks: { loto: true, grounding: false, ppe: true, ventilation: false },
      gaps: [
        "OISD-GDN-180: Electrostatic grounding checklist missing.",
        "OSHA 1910.146: Confined space ventilation check absent prior to casing removal."
      ]
    },
    {
      docName: "REG_Compressor_C-101_Standard.pdf",
      category: "OEM guidelines",
      safetyScore: 100,
      checks: { loto: true, grounding: true, ppe: true, ventilation: true },
      gaps: []
    }
  ]);

  // Defaults match latest benchmark / model card
  const [metrics, setMetrics] = useState({
    entity_accuracy: 82.7,
    query_accuracy: 92.6,
    kg_linkage: 91.8,
    time_to_answer: 2.8,
    compliance_gap_accuracy: 75.0
  });

  const fetchLiveMetrics = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/metrics", {
        headers: { "Authorization": "Bearer dev-key" }
      });
      if (res.ok) {
        const data = await res.json();
        setMetrics({
          entity_accuracy: data.entity_accuracy,
          query_accuracy: data.query_accuracy,
          kg_linkage: data.kg_linkage,
          time_to_answer: data.time_to_answer,
          compliance_gap_accuracy: data.compliance_gap_accuracy
        });
        if (data.compliance_reports && data.compliance_reports.length > 0) {
          setComplianceData(data.compliance_reports);
        }
      }
    } catch (e) {
      console.warn("Could not load live backend metrics, using fallback.", e);
    }
  };

  useEffect(() => {
    fetchLiveMetrics();
  }, []);

  const runDiagnostics = async () => {
    setLoading(true);
    await fetchLiveMetrics();
    setTimeout(() => setLoading(false), 600);
  };

  const metricCards = [
    { label: "RAG recall", value: `${metrics.entity_accuracy}%`, hint: "vs keyword baseline +20.5 pp", accent: "var(--accent)" },
    { label: "Bearing model", value: `${metrics.query_accuracy}%`, hint: "Real CWRU held-out accuracy", accent: "#a5b4fc" },
    { label: "KG linkage", value: `${metrics.kg_linkage}%`, hint: "Ontology coverage", accent: "#c084fc" },
    { label: "Median latency", value: `${metrics.time_to_answer}s`, hint: "End-to-end query time", accent: "var(--warning)" },
    { label: "Compliance guard", value: `${metrics.compliance_gap_accuracy}%`, hint: "Safety checklist coverage", accent: "var(--success)" },
  ];

  return (
    <div className="page-shell">
      <div className="page-header">
        <div>
          <div className="label">Operations</div>
          <h1 className="page-title" style={{ marginTop: 8 }}>Compliance & system control</h1>
          <p className="page-subtitle">
            Benchmark metrics and regulatory safety coverage for BPCL Mathura assets.
          </p>
        </div>
        <button className="btn btn-primary" onClick={runDiagnostics} disabled={loading}>
          {loading ? <RefreshCw size={14} style={{ animation: "spin 1s linear infinite" }} /> : <Play size={14} />}
          Run performance audit
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 20 }}>
        {metricCards.map((m) => (
          <div key={m.label} className="card" style={{ padding: "24px 22px", position: "relative", overflow: "hidden" }}>
            <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 2, background: m.accent, opacity: 0.85 }} />
            <div className="label" style={{ marginBottom: 14 }}>{m.label}</div>
            <div style={{ fontSize: 28, fontWeight: 560, letterSpacing: "-0.03em", lineHeight: 1 }}>
              {m.value}
            </div>
            <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 12, lineHeight: 1.45 }}>
              {m.hint}
            </p>
          </div>
        ))}
      </div>

      <div className="card card-pad">
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 28 }}>
          <ShieldAlert size={16} color="var(--accent)" />
          <h2 className="label" style={{ color: "var(--accent)", letterSpacing: "0.06em" }}>
            SOP safety audit
          </h2>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {complianceData.map((doc, idx) => (
            <div
              key={idx}
              style={{
                border: "1px solid var(--border)",
                background: "var(--bg-base)",
                borderRadius: "var(--r-md)",
                padding: "28px 28px",
                display: "grid",
                gridTemplateColumns: "1fr auto",
                gap: 32,
                alignItems: "start",
              }}
            >
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap", marginBottom: 16 }}>
                  <span style={{ fontSize: 14, fontWeight: 560 }}>{doc.docName}</span>
                  <span className="badge badge-default">{doc.category}</span>
                </div>

                <div style={{ display: "flex", flexWrap: "wrap", gap: 20, marginBottom: doc.gaps.length ? 20 : 0 }}>
                  {CHECK_LABELS.map(({ key, label }) => (
                    <div key={key} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <CheckCircle2
                        size={15}
                        color={doc.checks[key] ? "var(--accent)" : "var(--text-muted)"}
                        opacity={doc.checks[key] ? 1 : 0.35}
                      />
                      <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>{label}</span>
                    </div>
                  ))}
                </div>

                {doc.gaps.length > 0 && (
                  <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                    {doc.gaps.map((gap, gIdx) => (
                      <div
                        key={gIdx}
                        style={{
                          display: "flex",
                          gap: 12,
                          alignItems: "flex-start",
                          padding: "14px 16px",
                          borderRadius: "var(--r-sm)",
                          background: "rgba(245,158,11,0.06)",
                          border: "1px solid rgba(245,158,11,0.18)",
                        }}
                      >
                        <AlertTriangle size={15} color="var(--warning)" style={{ marginTop: 2, flexShrink: 0 }} />
                        <span style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.55 }}>{gap}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div style={{
                minWidth: 112,
                padding: "20px 18px",
                borderRadius: "var(--r-md)",
                border: "1px solid var(--border)",
                background: "var(--bg-surface)",
                textAlign: "center",
              }}>
                <div className="label" style={{ marginBottom: 10 }}>Safety</div>
                <div style={{
                  fontSize: 26,
                  fontWeight: 560,
                  letterSpacing: "-0.03em",
                  color: doc.safetyScore === 100 ? "var(--accent)" : doc.safetyScore >= 70 ? "var(--warning)" : "var(--danger)",
                }}>
                  {doc.safetyScore}%
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }
        @media (max-width: 1100px) {
          .page-shell > div:nth-child(2) { grid-template-columns: repeat(2, 1fr) !important; }
        }
      `}</style>
    </div>
  );
}
