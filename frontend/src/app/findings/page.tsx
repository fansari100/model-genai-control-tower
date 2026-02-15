"use client";

import { AlertTriangle, Search } from "lucide-react";
import { cn, statusColor, severityColor, humanize, formatDate } from "@/lib/utils";
import { findings as findingsApi } from "@/lib/api";
import { useApi } from "@/hooks/use-api";
import type { PaginatedResponse } from "@/lib/types";
import { useState } from "react";

const seedFindings = [
  { id: "f1", title: "Prompt injection bypass in multi-turn conversation", severity: "high", status: "open", source: "red_team", use_case: "WM Assistant", owasp_risk_id: "LLM01", remediation_owner: "AI Platform Team", remediation_due_date: "2026-03-01T00:00:00Z", created_at: "2026-02-10T00:00:00Z" },
  { id: "f2", title: "PII detected in model output for account query", severity: "critical", status: "in_progress", source: "evaluation", use_case: "WM Assistant", owasp_risk_id: "LLM06", remediation_owner: "AI Platform Team", remediation_due_date: "2026-02-20T00:00:00Z", created_at: "2026-02-08T00:00:00Z" },
  { id: "f3", title: "Meeting summarizer occasionally hallucinates action items", severity: "medium", status: "open", source: "evaluation", use_case: "Debrief", owasp_risk_id: "LLM09", remediation_owner: "WM Technology", remediation_due_date: "2026-03-15T00:00:00Z", created_at: "2026-02-11T00:00:00Z" },
  { id: "f4", title: "Agent tool call exceeded permission scope", severity: "high", status: "mitigated", source: "red_team", use_case: "Research Agent", owasp_risk_id: "ASI02", remediation_owner: "AI Platform Team", created_at: "2026-02-12T00:00:00Z" },
  { id: "f5", title: "Model version not logged in 3% of requests", severity: "medium", status: "in_progress", source: "monitoring", use_case: "Debrief", remediation_owner: "WM Technology", created_at: "2026-02-13T00:00:00Z" },
  { id: "f6", title: "Retrieval corpus contains outdated policy documents", severity: "low", status: "open", source: "manual", use_case: "WM Assistant", nist_consideration: "content_provenance", remediation_owner: "Knowledge Management", created_at: "2026-02-05T00:00:00Z" },
  { id: "f7", title: "Agent memory persistence exceeds approved TTL", severity: "medium", status: "open", source: "evaluation", use_case: "Research Agent", owasp_risk_id: "ASI06", remediation_owner: "AI Platform Team", created_at: "2026-02-14T00:00:00Z" },
];

export default function FindingsPage() {
  const [search, setSearch] = useState("");

  const { data } = useApi<PaginatedResponse<any>>(
    () => findingsApi.list(search ? `search=${search}` : ""),
    { items: seedFindings, total: seedFindings.length, page: 1, page_size: 20, total_pages: 1 },
    [search],
  );

  const allFindings = data?.items ?? seedFindings;
  const filtered = allFindings.filter((f: any) =>
    f.title.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Findings Register</h1>
          <p className="text-sm text-gray-500 mt-1">Issues discovered during evaluation, red-teaming, and monitoring</p>
        </div>
      </div>

      <div className="grid grid-cols-5 gap-4">
        {(["critical", "high", "medium", "low", "informational"] as const).map((sev) => {
          const count = allFindings.filter((f: any) => f.severity === sev && ["open", "in_progress"].includes(f.status)).length;
          return (
            <div key={sev} className="rounded-lg border bg-white p-4 text-center">
              <p className={cn("text-2xl font-bold", sev === "critical" ? "text-red-600" : sev === "high" ? "text-orange-600" : sev === "medium" ? "text-yellow-600" : "text-gray-600")}>
                {count}
              </p>
              <p className="text-xs text-gray-500">Open {humanize(sev)}</p>
            </div>
          );
        })}
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
        <input type="text" placeholder="Search findings..." value={search} onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-lg border border-gray-300 bg-white py-2 pl-10 pr-4 text-sm focus:border-primary focus:outline-none" />
      </div>

      <div className="space-y-3">
        {filtered.map((finding) => (
          <div key={finding.id} className="rounded-xl border bg-white p-5 shadow-sm hover:shadow-md transition-shadow cursor-pointer">
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <AlertTriangle className={cn("h-5 w-5 mt-0.5", finding.severity === "critical" ? "text-red-600" : finding.severity === "high" ? "text-orange-500" : "text-yellow-500")} />
                <div>
                  <h3 className="text-sm font-semibold text-gray-900">{finding.title}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={cn("inline-flex rounded-full px-2 py-0.5 text-xs font-medium", severityColor(finding.severity))}>
                      {humanize(finding.severity)}
                    </span>
                    <span className={cn("inline-flex rounded-full px-2 py-0.5 text-xs font-medium", statusColor(finding.status))}>
                      {humanize(finding.status)}
                    </span>
                    <span className="text-xs text-gray-500">· {finding.use_case}</span>
                    {finding.owasp_risk_id && (
                      <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-mono text-gray-600">{finding.owasp_risk_id}</span>
                    )}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-500">Source: {humanize(finding.source)}</p>
                {finding.remediation_due_date && (
                  <p className="text-xs text-gray-400 mt-1">Due: {formatDate(finding.remediation_due_date)}</p>
                )}
              </div>
            </div>
            <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
              <span className="text-xs text-gray-500">Owner: {finding.remediation_owner}</span>
              <span className="text-xs text-gray-400">Created: {formatDate(finding.created_at)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
