"use client";

import { FileCheck2, Download, Shield, CheckCircle2, AlertTriangle, Clock } from "lucide-react";
import { cn, statusColor, riskColor, humanize } from "@/lib/utils";

const certPacks = [
  {
    id: "CP-uc1-20260214",
    use_case: "WM Assistant – Internal Q&A",
    risk_rating: "high",
    status: "approved",
    sections: 8,
    findings: { total: 3, open_critical: 0 },
    approvals: 3,
    generated: "2026-02-14T10:00:00Z",
  },
  {
    id: "CP-uc2-20260213",
    use_case: "Debrief – Meeting Summarizer",
    risk_rating: "high",
    status: "conditional",
    sections: 8,
    findings: { total: 5, open_critical: 1 },
    approvals: 2,
    generated: "2026-02-13T14:00:00Z",
  },
  {
    id: "CP-uc3-20260212",
    use_case: "Research Agent – Multi-Step Analysis",
    risk_rating: "critical",
    status: "pending",
    sections: 8,
    findings: { total: 8, open_critical: 3 },
    approvals: 0,
    generated: "2026-02-12T09:00:00Z",
  },
];

const certSections = [
  "Use Case Summary & Risk Assessment",
  "NIST AI 600-1 GenAI Profile Compliance",
  "OWASP LLM Top 10 & Agentic Top 10 Mapping",
  "Pre-Deployment Testing Results",
  "Findings Register",
  "Governance Approval Record",
  "Ongoing Monitoring Plan",
  "ISO/IEC 42001 PDCA Lifecycle Mapping",
];

export default function CertificationsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Certification Packs</h1>
          <p className="text-sm text-gray-500 mt-1">
            Audit-grade certification evidence for GenAI use cases
          </p>
        </div>
        <button className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90">
          <FileCheck2 className="h-4 w-4" /> Generate New Pack
        </button>
      </div>

      {/* Pack outline */}
      <div className="rounded-xl border bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Certification Pack Contents</h3>
        <div className="grid grid-cols-2 gap-2 lg:grid-cols-4">
          {certSections.map((section, i) => (
            <div key={section} className="flex items-center gap-2 rounded-lg bg-gray-50 p-3 border border-gray-100">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs text-white font-medium">{i + 1}</span>
              <span className="text-xs text-gray-700">{section}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Packs list */}
      <div className="space-y-4">
        {certPacks.map((pack) => (
          <div key={pack.id} className="rounded-xl border bg-white p-6 shadow-sm">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-4">
                <div className={cn(
                  "flex h-12 w-12 items-center justify-center rounded-lg",
                  pack.status === "approved" ? "bg-green-100" : pack.status === "conditional" ? "bg-yellow-100" : "bg-gray-100"
                )}>
                  {pack.status === "approved" ? (
                    <CheckCircle2 className="h-6 w-6 text-green-600" />
                  ) : pack.status === "conditional" ? (
                    <AlertTriangle className="h-6 w-6 text-yellow-600" />
                  ) : (
                    <Clock className="h-6 w-6 text-gray-400" />
                  )}
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-gray-900">{pack.use_case}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs font-mono text-gray-500">{pack.id}</span>
                    <span className={cn("inline-flex rounded-full px-2 py-0.5 text-xs font-medium", riskColor(pack.risk_rating))}>
                      {humanize(pack.risk_rating)} Risk
                    </span>
                    <span className={cn("inline-flex rounded-full px-2 py-0.5 text-xs font-medium", statusColor(pack.status))}>
                      {humanize(pack.status)}
                    </span>
                  </div>
                </div>
              </div>
              <button className="inline-flex items-center gap-2 rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50">
                <Download className="h-4 w-4" /> Download PDF
              </button>
            </div>

            <div className="grid grid-cols-4 gap-4 mt-4 pt-4 border-t border-gray-100">
              <div className="text-center">
                <p className="text-lg font-bold text-gray-900">{pack.sections}</p>
                <p className="text-xs text-gray-500">Sections</p>
              </div>
              <div className="text-center">
                <p className="text-lg font-bold text-gray-900">{pack.findings.total}</p>
                <p className="text-xs text-gray-500">Findings</p>
              </div>
              <div className="text-center">
                <p className={cn("text-lg font-bold", pack.findings.open_critical > 0 ? "text-red-600" : "text-green-600")}>
                  {pack.findings.open_critical}
                </p>
                <p className="text-xs text-gray-500">Open Critical</p>
              </div>
              <div className="text-center">
                <p className="text-lg font-bold text-gray-900">{pack.approvals}</p>
                <p className="text-xs text-gray-500">Approvals</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
