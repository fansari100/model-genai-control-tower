"use client";

import { useState } from "react";
import { Wrench, Plus, Search, CheckCircle2 } from "lucide-react";
import { cn, statusColor, humanize, formatDate } from "@/lib/utils";
import { tools as toolsApi } from "@/lib/api";
import { useApi } from "@/hooks/use-api";
import type { Tool, PaginatedResponse } from "@/lib/types";

const seedTools: Tool[] = [
  { id: "t1", name: "Portfolio Valuation Calculator", version: "4.2", category: "euc_spreadsheet", criticality: "critical", status: "attested", owner: "Portfolio Analytics", last_attestation_date: "2025-11-15T00:00:00Z", next_attestation_date: "2026-11-15T00:00:00Z", created_at: "2020-03-01T00:00:00Z" },
  { id: "t2", name: "Risk Metrics VBA Macro", version: "2.1", category: "euc_vba", criticality: "high", status: "attestation_due", owner: "Risk Management", next_attestation_date: "2026-03-01T00:00:00Z", created_at: "2019-06-15T00:00:00Z" },
  { id: "t3", name: "Client Suitability Scorer", version: "1.5", category: "system_calculator", criticality: "critical", status: "attested", owner: "Compliance", last_attestation_date: "2025-09-01T00:00:00Z", next_attestation_date: "2026-09-01T00:00:00Z", created_at: "2021-01-10T00:00:00Z" },
  { id: "t4", name: "Trade Reconciliation Script", version: "3.0", category: "script", criticality: "high", status: "attested", owner: "Operations", last_attestation_date: "2025-12-01T00:00:00Z", next_attestation_date: "2026-12-01T00:00:00Z", created_at: "2018-08-20T00:00:00Z" },
  { id: "t5", name: "Performance Attribution Dashboard", version: "2.3", category: "dashboard", criticality: "medium", status: "under_review", owner: "Reporting", created_at: "2022-04-15T00:00:00Z" },
  { id: "t6", name: "CRM Integration API (Salesforce)", version: "1.0", category: "api_service", criticality: "high", status: "attested", owner: "WM Technology", last_attestation_date: "2026-01-15T00:00:00Z", next_attestation_date: "2027-01-15T00:00:00Z", created_at: "2024-06-01T00:00:00Z" },
  { id: "t7", name: "Knowledge Base Search Tool", version: "1.2", category: "agent_tool", criticality: "medium", status: "attested", owner: "AI Platform Team", last_attestation_date: "2026-01-01T00:00:00Z", next_attestation_date: "2026-07-01T00:00:00Z", created_at: "2025-01-01T00:00:00Z" },
  { id: "t8", name: "Fee Calculator", version: "5.1", category: "euc_spreadsheet", criticality: "critical", status: "attestation_overdue", owner: "Billing Operations", next_attestation_date: "2026-01-01T00:00:00Z", created_at: "2017-09-01T00:00:00Z" },
];

const criticalityColor: Record<string, string> = {
  critical: "bg-red-100 text-red-800",
  high: "bg-orange-100 text-orange-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-green-100 text-green-800",
};

export default function ToolsPage() {
  const [search, setSearch] = useState("");

  const { data } = useApi<PaginatedResponse<Tool>>(
    () => toolsApi.list(search ? `search=${search}` : ""),
    { items: seedTools, total: seedTools.length, page: 1, page_size: 20, total_pages: 1 },
    [search],
  );

  const allTools = data?.items ?? seedTools;
  const filtered = allTools.filter((t) =>
    t.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tools & EUC Inventory</h1>
          <p className="text-sm text-gray-500 mt-1">
            Non-model tools, spreadsheets, scripts, and system calculators under governance
          </p>
        </div>
        <button className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90">
          <Plus className="h-4 w-4" /> Register Tool
        </button>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="rounded-lg border bg-white p-4 text-center">
          <p className="text-2xl font-bold text-gray-900">{allTools.length}</p>
          <p className="text-xs text-gray-500">Total Tools</p>
        </div>
        <div className="rounded-lg border bg-white p-4 text-center">
          <p className="text-2xl font-bold text-green-600">{allTools.filter(t => t.status === "attested").length}</p>
          <p className="text-xs text-gray-500">Attested</p>
        </div>
        <div className="rounded-lg border bg-white p-4 text-center">
          <p className="text-2xl font-bold text-yellow-600">{allTools.filter(t => t.status === "attestation_due").length}</p>
          <p className="text-xs text-gray-500">Due</p>
        </div>
        <div className="rounded-lg border bg-white p-4 text-center">
          <p className="text-2xl font-bold text-red-600">{allTools.filter(t => t.status === "attestation_overdue").length}</p>
          <p className="text-xs text-gray-500">Overdue</p>
        </div>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Search tools..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-lg border border-gray-300 bg-white py-2 pl-10 pr-4 text-sm focus:border-primary focus:outline-none"
        />
      </div>

      <div className="overflow-hidden rounded-xl border bg-white shadow-sm">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Tool</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Category</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Criticality</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Owner</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Last Attested</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Next Due</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {filtered.map((tool) => (
              <tr key={tool.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <Wrench className="h-5 w-5 text-gray-400" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">{tool.name}</p>
                      <p className="text-xs text-gray-500">v{tool.version}</p>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 text-sm text-gray-700">{humanize(tool.category)}</td>
                <td className="px-6 py-4">
                  <span className={cn("inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium", criticalityColor[tool.criticality])}>
                    {humanize(tool.criticality)}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span className={cn("inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium", statusColor(tool.status))}>
                    {humanize(tool.status)}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-700">{tool.owner}</td>
                <td className="px-6 py-4 text-sm text-gray-500">{formatDate(tool.last_attestation_date)}</td>
                <td className="px-6 py-4 text-sm text-gray-500">{formatDate(tool.next_attestation_date)}</td>
                <td className="px-6 py-4">
                  <button className="inline-flex items-center gap-1 rounded-md bg-green-50 px-3 py-1 text-xs font-medium text-green-700 hover:bg-green-100">
                    <CheckCircle2 className="h-3 w-3" /> Attest
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
