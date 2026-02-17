"use client";

import { FlaskConical, Play, Search } from "lucide-react";
import { cn, statusColor, humanize, formatDate } from "@/lib/utils";
import { evaluations as evalsApi } from "@/lib/api";
import { useApi } from "@/hooks/use-api";
import type { EvaluationRun, PaginatedResponse } from "@/lib/types";
import { useState } from "react";

const seedEvals = [
  { id: "e1", name: "WM Assistant – Quality Suite", eval_type: "quality_correctness", status: "completed", use_case_id: "uc1", total_tests: 50, passed: 48, failed: 2, pass_rate: 0.96, started_at: "2026-02-10T10:00:00Z", completed_at: "2026-02-10T10:15:00Z" },
  { id: "e2", name: "WM Assistant – Red Team (promptfoo)", eval_type: "red_team_promptfoo", status: "completed", use_case_id: "uc1", total_tests: 120, passed: 115, failed: 5, pass_rate: 0.958, started_at: "2026-02-10T11:00:00Z", completed_at: "2026-02-10T11:45:00Z" },
  { id: "e3", name: "Debrief – Summarization Faithfulness", eval_type: "rag_groundedness", status: "completed", use_case_id: "uc2", total_tests: 30, passed: 28, failed: 2, pass_rate: 0.933, started_at: "2026-02-11T09:00:00Z", completed_at: "2026-02-11T09:20:00Z" },
  { id: "e4", name: "Research Agent – Agentic Safety", eval_type: "agentic_safety", status: "running", use_case_id: "uc3", total_tests: 40, passed: 20, failed: 1, pass_rate: null, started_at: "2026-02-14T08:00:00Z" },
  { id: "e5", name: "Research Agent – garak Vulnerability Scan", eval_type: "vulnerability_garak", status: "completed", use_case_id: "uc3", total_tests: 200, passed: 192, failed: 8, pass_rate: 0.96, started_at: "2026-02-12T14:00:00Z", completed_at: "2026-02-12T14:30:00Z" },
  { id: "e6", name: "Debrief – Operational Controls", eval_type: "operational_controls", status: "completed", use_case_id: "uc2", total_tests: 5, passed: 5, failed: 0, pass_rate: 1.0, started_at: "2026-02-13T09:00:00Z", completed_at: "2026-02-13T09:05:00Z" },
  { id: "e7", name: "WM Assistant – PyRIT Security", eval_type: "red_team_pyrit", status: "completed", use_case_id: "uc1", total_tests: 10, passed: 9, failed: 1, pass_rate: 0.9, started_at: "2026-02-13T10:00:00Z", completed_at: "2026-02-13T10:30:00Z" },
  { id: "e8", name: "Daily Regression – WM Assistant", eval_type: "regression", status: "pending", use_case_id: "uc1", total_tests: 0, passed: 0, failed: 0, pass_rate: null, started_at: null },
];

const evalTypeColors: Record<string, string> = {
  quality_correctness: "bg-blue-100 text-blue-800",
  safety_security: "bg-red-100 text-red-800",
  red_team_promptfoo: "bg-red-100 text-red-800",
  red_team_pyrit: "bg-red-100 text-red-800",
  vulnerability_garak: "bg-orange-100 text-orange-800",
  rag_groundedness: "bg-green-100 text-green-800",
  operational_controls: "bg-teal-100 text-teal-800",
  agentic_safety: "bg-purple-100 text-purple-800",
  regression: "bg-gray-100 text-gray-800",
  canary: "bg-yellow-100 text-yellow-800",
};

export default function EvaluationsPage() {
  const [search, setSearch] = useState("");

  const { data } = useApi<PaginatedResponse<any>>(
    () => evalsApi.list(search ? `search=${search}` : ""),
    { items: seedEvals, total: seedEvals.length, page: 1, page_size: 20, total_pages: 1 },
    [search],
  );

  const allEvals = data?.items ?? seedEvals;
  const filtered = allEvals.filter((e: any) =>
    e.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Evaluations</h1>
          <p className="text-sm text-gray-500 mt-1">
            Quality, safety, security, and compliance test runs
          </p>
        </div>
        <button className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90">
          <Play className="h-4 w-4" /> Trigger Evaluation
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-6 gap-4">
        <div className="rounded-lg border bg-white p-4 text-center">
          <p className="text-2xl font-bold text-gray-900">{allEvals.length}</p>
          <p className="text-xs text-gray-500">Total Runs</p>
        </div>
        <div className="rounded-lg border bg-white p-4 text-center">
          <p className="text-2xl font-bold text-green-600">{allEvals.filter((e: any) => e.status === "completed").length}</p>
          <p className="text-xs text-gray-500">Completed</p>
        </div>
        <div className="rounded-lg border bg-white p-4 text-center">
          <p className="text-2xl font-bold text-blue-600">{allEvals.filter((e: any) => e.status === "running").length}</p>
          <p className="text-xs text-gray-500">Running</p>
        </div>
        <div className="rounded-lg border bg-white p-4 text-center">
          <p className="text-2xl font-bold text-yellow-600">{allEvals.filter((e: any) => e.status === "pending").length}</p>
          <p className="text-xs text-gray-500">Pending</p>
        </div>
        <div className="rounded-lg border bg-white p-4 text-center">
          <p className="text-2xl font-bold text-gray-900">
            {(() => {
              const completed = allEvals.filter((e: any) => e.pass_rate !== null);
              const avg = completed.length > 0 ? completed.reduce((sum, e) => sum + (e.pass_rate || 0), 0) / completed.length : 0;
              return `${(avg * 100).toFixed(1)}%`;
            })()}
          </p>
          <p className="text-xs text-gray-500">Avg Pass Rate</p>
        </div>
        <div className="rounded-lg border bg-white p-4 text-center">
          <p className="text-2xl font-bold text-red-600">{allEvals.reduce((sum: number, e: any) => sum + (e.failed || 0), 0)}</p>
          <p className="text-xs text-gray-500">Total Failures</p>
        </div>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
        <input type="text" placeholder="Search evaluations..." value={search} onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-lg border border-gray-300 bg-white py-2 pl-10 pr-4 text-sm focus:border-primary focus:outline-none" />
      </div>

      <div className="overflow-hidden rounded-xl border bg-white shadow-sm">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Evaluation</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Tests</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Pass Rate</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Started</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {filtered.map((ev) => (
              <tr key={ev.id} className="hover:bg-gray-50 cursor-pointer">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <FlaskConical className="h-5 w-5 text-gray-400" />
                    <span className="text-sm font-medium text-gray-900">{ev.name}</span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span className={cn("inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium", evalTypeColors[ev.eval_type] || "bg-gray-100 text-gray-800")}>
                    {humanize(ev.eval_type)}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span className={cn("inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium", statusColor(ev.status))}>
                    {humanize(ev.status)}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span className="text-sm text-gray-700">
                    <span className="text-green-600 font-medium">{ev.passed}</span>
                    {" / "}
                    <span className="text-gray-500">{ev.total_tests}</span>
                    {ev.failed > 0 && <span className="text-red-600 font-medium ml-1">({ev.failed} failed)</span>}
                  </span>
                </td>
                <td className="px-6 py-4">
                  {ev.pass_rate !== null ? (
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-20 rounded-full bg-gray-100">
                        <div className={cn("h-2 rounded-full", ev.pass_rate >= 0.95 ? "bg-green-500" : ev.pass_rate >= 0.90 ? "bg-yellow-500" : "bg-red-500")}
                          style={{ width: `${ev.pass_rate * 100}%` }} />
                      </div>
                      <span className="text-sm font-medium text-gray-900">{(ev.pass_rate * 100).toFixed(1)}%</span>
                    </div>
                  ) : (
                    <span className="text-sm text-gray-400">—</span>
                  )}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">{formatDate(ev.started_at || undefined)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
