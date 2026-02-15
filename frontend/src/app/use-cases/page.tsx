"use client";

import { useState } from "react";
import { Sparkles, Plus, Search, ArrowRight, Shield } from "lucide-react";
import { cn, statusColor, riskColor, humanize, formatDate } from "@/lib/utils";
import { useCases as useCasesApi } from "@/lib/api";
import { useApi } from "@/hooks/use-api";
import type { GenAIUseCase, PaginatedResponse } from "@/lib/types";

const seedUseCases: GenAIUseCase[] = [
  { id: "uc1", name: "WM Assistant – Internal Q&A", version: "2.1.0", category: "rag_qa", status: "approved", risk_rating: "high", data_classification: "confidential", client_facing: false, uses_agents: false, uses_rag: true, uses_tools: true, uses_memory: false, requires_human_in_loop: false, owner: "AI Platform Team", business_unit: "Wealth Management", required_test_suites: ["quality_correctness", "rag_groundedness", "safety_security", "red_team_promptfoo", "operational_controls"], created_at: "2024-03-15T00:00:00Z" },
  { id: "uc2", name: "Debrief – Meeting Summarizer", version: "1.3.0", category: "summarization", status: "monitoring", risk_rating: "high", data_classification: "pii", client_facing: true, uses_agents: false, uses_rag: false, uses_tools: true, uses_memory: false, requires_human_in_loop: true, owner: "WM Technology", business_unit: "Wealth Management", required_test_suites: ["quality_correctness", "safety_security", "red_team_promptfoo", "vulnerability_garak", "operational_controls", "regression"], created_at: "2024-06-01T00:00:00Z" },
  { id: "uc3", name: "Research Agent – Multi-Step Analysis", version: "0.5.0", category: "agent_workflow", status: "testing", risk_rating: "critical", data_classification: "confidential", client_facing: false, uses_agents: true, uses_rag: true, uses_tools: true, uses_memory: true, requires_human_in_loop: true, owner: "AI Platform Team", business_unit: "Wealth Management", required_test_suites: ["quality_correctness", "rag_groundedness", "safety_security", "red_team_promptfoo", "red_team_pyrit", "vulnerability_garak", "agentic_safety", "operational_controls", "regression"], created_at: "2025-01-10T00:00:00Z" },
  { id: "uc4", name: "Client Email Drafting", version: "1.0.0", category: "content_generation", status: "intake", risk_rating: "medium", data_classification: "pii", client_facing: true, uses_agents: false, uses_rag: false, uses_tools: false, uses_memory: false, requires_human_in_loop: true, owner: "WM Technology", business_unit: "Wealth Management", created_at: "2025-02-01T00:00:00Z" },
  { id: "uc5", name: "Document Classifier", version: "1.2.0", category: "classification", status: "approved", risk_rating: "low", data_classification: "internal", client_facing: false, uses_agents: false, uses_rag: false, uses_tools: false, uses_memory: false, requires_human_in_loop: false, owner: "Operations", business_unit: "Operations", created_at: "2024-08-20T00:00:00Z" },
];

export default function UseCasesPage() {
  const [search, setSearch] = useState("");

  const { data } = useApi<PaginatedResponse<GenAIUseCase>>(
    () => useCasesApi.list(search ? `search=${search}` : ""),
    { items: seedUseCases, total: seedUseCases.length, page: 1, page_size: 20, total_pages: 1 },
    [search],
  );

  const allUseCases = data?.items ?? seedUseCases;
  const filtered = allUseCases.filter((uc) =>
    uc.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">GenAI Use Cases</h1>
          <p className="text-sm text-gray-500 mt-1">
            Governed GenAI applications and workflows
          </p>
        </div>
        <button className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90">
          <Plus className="h-4 w-4" /> New Intake
        </button>
      </div>

      {/* Pipeline Overview */}
      <div className="rounded-xl border bg-white p-4 shadow-sm">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Certification Pipeline</h3>
        <div className="flex items-center gap-2 overflow-x-auto">
          {["intake", "risk_assessment", "testing", "pending_approval", "approved", "monitoring"].map((stage, i) => {
            const count = allUseCases.filter(uc => uc.status === stage).length;
            return (
              <div key={stage} className="flex items-center gap-2">
                <div className={cn("flex flex-col items-center rounded-lg border px-4 py-2 min-w-[120px]", count > 0 ? "border-primary bg-primary/5" : "border-gray-200")}>
                  <span className="text-lg font-bold text-gray-900">{count}</span>
                  <span className="text-xs text-gray-500">{humanize(stage)}</span>
                </div>
                {i < 5 && <ArrowRight className="h-4 w-4 text-gray-300 flex-shrink-0" />}
              </div>
            );
          })}
        </div>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Search use cases..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-lg border border-gray-300 bg-white py-2 pl-10 pr-4 text-sm focus:border-primary focus:outline-none"
        />
      </div>

      {/* Cards View */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {filtered.map((uc) => (
          <div key={uc.id} className="rounded-xl border bg-white p-6 shadow-sm hover:shadow-md transition-shadow cursor-pointer">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <Sparkles className="h-5 w-5 text-indigo-500" />
                <div>
                  <h3 className="text-sm font-semibold text-gray-900">{uc.name}</h3>
                  <p className="text-xs text-gray-500">v{uc.version} · {humanize(uc.category)}</p>
                </div>
              </div>
              <span className={cn("inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium", riskColor(uc.risk_rating))}>
                {humanize(uc.risk_rating)} Risk
              </span>
            </div>

            <div className="flex items-center gap-2 mb-3">
              <span className={cn("inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium", statusColor(uc.status))}>
                {humanize(uc.status)}
              </span>
              <span className="text-xs text-gray-500">·</span>
              <span className="text-xs text-gray-500">{humanize(uc.data_classification)} data</span>
              {uc.client_facing && <span className="inline-flex rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">Client-Facing</span>}
            </div>

            {/* Architecture flags */}
            <div className="flex flex-wrap gap-1.5 mb-3">
              {uc.uses_rag && <span className="rounded-md bg-blue-50 px-2 py-0.5 text-xs text-blue-700">RAG</span>}
              {uc.uses_agents && <span className="rounded-md bg-purple-50 px-2 py-0.5 text-xs text-purple-700">Agents</span>}
              {uc.uses_tools && <span className="rounded-md bg-green-50 px-2 py-0.5 text-xs text-green-700">Tools</span>}
              {uc.uses_memory && <span className="rounded-md bg-orange-50 px-2 py-0.5 text-xs text-orange-700">Memory</span>}
              {uc.requires_human_in_loop && <span className="rounded-md bg-teal-50 px-2 py-0.5 text-xs text-teal-700">HITL Required</span>}
            </div>

            {/* Required test suites */}
            {uc.required_test_suites && uc.required_test_suites.length > 0 && (
              <div className="border-t border-gray-100 pt-3 mt-3">
                <p className="text-xs font-medium text-gray-500 mb-1.5">Required Test Suites</p>
                <div className="flex flex-wrap gap-1">
                  {uc.required_test_suites.map((suite) => (
                    <span key={suite} className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-600">{humanize(suite)}</span>
                  ))}
                </div>
              </div>
            )}

            <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
              <span className="text-xs text-gray-500">Owner: {uc.owner}</span>
              <span className="text-xs text-gray-400">{formatDate(uc.created_at)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
