"use client";

import { useState } from "react";
import { Cpu, Plus, Search } from "lucide-react";
import { cn, statusColor, riskColor, humanize, formatDate } from "@/lib/utils";
import { models as modelsApi } from "@/lib/api";
import { useApi } from "@/hooks/use-api";
import type { Model, PaginatedResponse } from "@/lib/types";

const seedModels: Model[] = [
  { id: "1", name: "GPT-5.2", version: "2025-12-11", model_type: "llm", deployment: "vendor_api", status: "approved", risk_tier: "tier_2_high", owner: "AI Platform Team", vendor_id: "v-openai", provider_model_id: "gpt-5.2-2025-12-11", created_at: "2024-06-15T00:00:00Z" },
  { id: "2", name: "Claude Opus 4.6", version: "20260203", model_type: "llm", deployment: "vendor_api", status: "under_review", risk_tier: "tier_2_high", owner: "AI Platform Team", vendor_id: "v-anthropic", provider_model_id: "claude-opus-4-20260203", created_at: "2025-01-10T00:00:00Z" },
  { id: "3", name: "Gemini 3 Pro", version: "2026-01-21", model_type: "llm", deployment: "vendor_api", status: "approved", risk_tier: "tier_2_high", owner: "AI Platform Team", vendor_id: "v-google", provider_model_id: "gemini-3-pro-2026-01-21", created_at: "2026-01-25T00:00:00Z" },
  { id: "4", name: "WM Portfolio Optimizer", version: "3.2.1", model_type: "ml_traditional", deployment: "on_premise", status: "approved", risk_tier: "tier_1_critical", owner: "Quantitative Analytics", created_at: "2023-03-20T00:00:00Z" },
  { id: "5", name: "Client Risk Scorer", version: "2.0.0", model_type: "statistical", deployment: "on_premise", status: "approved", risk_tier: "tier_3_medium", owner: "Risk Management", created_at: "2022-11-01T00:00:00Z" },
  { id: "6", name: "text-embedding-3-large", version: "1.0", model_type: "deep_learning", deployment: "vendor_api", status: "approved", risk_tier: "tier_4_low", owner: "AI Platform Team", vendor_id: "v-openai", created_at: "2024-09-01T00:00:00Z" },
  { id: "7", name: "Meeting Summarizer (fine-tuned)", version: "1.1.0", model_type: "llm", deployment: "self_hosted", status: "intake", risk_tier: "tier_3_medium", owner: "WM Technology", created_at: "2025-02-01T00:00:00Z" },
];

export default function ModelsPage() {
  const [search, setSearch] = useState("");

  const { data, loading } = useApi<PaginatedResponse<Model>>(
    () => modelsApi.list(search ? `search=${search}` : ""),
    { items: seedModels, total: seedModels.length, page: 1, page_size: 20, total_pages: 1 },
    [search],
  );

  const items = data?.items ?? seedModels;
  const filtered = items.filter((m) =>
    m.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Model Inventory</h1>
          <p className="text-sm text-gray-500 mt-1">
            Statistical, ML, LLM, and vendor models under governance
          </p>
        </div>
        <button className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90">
          <Plus className="h-4 w-4" /> Register Model
        </button>
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search models..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-gray-300 bg-white py-2 pl-10 pr-4 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border bg-white shadow-sm">
        {loading && <div className="p-4 text-center text-sm text-gray-400">Loading...</div>}
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Model</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Deployment</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Risk Tier</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Owner</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Registered</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {filtered.map((model) => (
              <tr key={model.id} className="hover:bg-gray-50 cursor-pointer">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <Cpu className="h-5 w-5 text-gray-400" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">{model.name}</p>
                      <p className="text-xs text-gray-500">v{model.version}</p>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 text-sm text-gray-700">{humanize(model.model_type)}</td>
                <td className="px-6 py-4 text-sm text-gray-700">{humanize(model.deployment)}</td>
                <td className="px-6 py-4">
                  <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", statusColor(model.status))}>{humanize(model.status)}</span>
                </td>
                <td className="px-6 py-4">
                  <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", riskColor(model.risk_tier))}>{humanize(model.risk_tier)}</span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-700">{model.owner}</td>
                <td className="px-6 py-4 text-sm text-gray-500">{formatDate(model.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
