"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Cpu,
  Wrench,
  Sparkles,
  AlertTriangle,
  FlaskConical,
  Shield,
  TrendingUp,
  FileCheck2,
  RefreshCw,
} from "lucide-react";
import { cn, humanize, riskColor, statusColor } from "@/lib/utils";
import { dashboard as dashboardApi } from "@/lib/api";

// Seed data used as initial state until the API responds.
const initialSummary = {
  inventory: {
    models: { total: 7, by_status: { approved: 5, under_review: 1, intake: 1 } },
    tools: { total: 8, by_status: { attested: 5, attestation_due: 1, under_review: 1, attestation_overdue: 1 } },
    use_cases: {
      total: 8,
      by_status: { approved: 3, testing: 2, intake: 2, monitoring: 1 },
      by_risk: { critical: 1, high: 3, medium: 3, low: 1 },
    },
  },
  risk_posture: {
    open_critical_findings: 2,
    total_findings: 7,
    avg_eval_pass_rate: 0.95,
    total_evaluations: 8,
  },
  compliance: {
    frameworks: [
      "SR 11-7 / OCC",
      "NIST AI 600-1",
      "OWASP LLM Top 10 2025",
      "OWASP Agentic Top 10 2026",
      "ISO/IEC 42001",
      "MITRE ATLAS",
      "FINRA GenAI Controls",
    ],
    status: "active",
  },
};

function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: any;
  color: string;
}) {
  return (
    <div className="rounded-xl border bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="mt-1 text-3xl font-bold text-gray-900">{value}</p>
          {subtitle && <p className="mt-1 text-xs text-gray-400">{subtitle}</p>}
        </div>
        <div className={cn("flex h-12 w-12 items-center justify-center rounded-lg", color)}>
          <Icon className="h-6 w-6 text-white" />
        </div>
      </div>
    </div>
  );
}

function StatusBreakdown({
  title,
  data,
}: {
  title: string;
  data: Record<string, number>;
}) {
  const total = Object.values(data).reduce((a, b) => a + b, 0);
  return (
    <div className="rounded-xl border bg-white p-6 shadow-sm">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">{title}</h3>
      <div className="space-y-3">
        {Object.entries(data).map(([status, count]) => (
          <div key={status} className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", statusColor(status))}>
                {humanize(status)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-900">{count}</span>
              <div className="h-2 w-16 rounded-full bg-gray-100">
                <div
                  className={cn("h-2 rounded-full", statusColor(status).includes("green") ? "bg-green-500" : statusColor(status).includes("blue") ? "bg-blue-500" : statusColor(status).includes("yellow") ? "bg-yellow-500" : statusColor(status).includes("red") ? "bg-red-500" : "bg-gray-400")}
                  style={{ width: `${total > 0 ? (count / total) * 100 : 0}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [summary, setSummary] = useState(initialSummary);
  const [loading, setLoading] = useState(false);
  const [apiConnected, setApiConnected] = useState(false);

  const fetchLive = useCallback(async () => {
    setLoading(true);
    try {
      const data = await dashboardApi.getSummary();
      setSummary(data);
      setApiConnected(true);
    } catch {
      // API not running — retain initial data
      setApiConnected(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchLive(); }, [fetchLive]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Control Tower Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">
            Unified view of model, tool, and GenAI governance posture
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium", apiConnected ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800")}>
            <span className={cn("h-1.5 w-1.5 rounded-full", apiConnected ? "bg-green-500" : "bg-yellow-500")} />
            {apiConnected ? "API Connected" : "Offline"}
          </span>
          <button onClick={fetchLive} disabled={loading} className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50">
            <RefreshCw className={cn("h-3 w-3", loading && "animate-spin")} /> Refresh
          </button>
        </div>
      </div>

      {/* Top-level stats */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Models"
          value={summary.inventory.models.total}
          subtitle="Vendor + Internal models"
          icon={Cpu}
          color="bg-blue-600"
        />
        <StatCard
          title="Tools & EUCs"
          value={summary.inventory.tools.total}
          subtitle="Non-model tools under governance"
          icon={Wrench}
          color="bg-purple-600"
        />
        <StatCard
          title="GenAI Use Cases"
          value={summary.inventory.use_cases.total}
          subtitle="Active GenAI applications"
          icon={Sparkles}
          color="bg-indigo-600"
        />
        <StatCard
          title="Open Critical Findings"
          value={summary.risk_posture.open_critical_findings}
          subtitle={`of ${summary.risk_posture.total_findings} total findings`}
          icon={AlertTriangle}
          color={summary.risk_posture.open_critical_findings > 0 ? "bg-red-600" : "bg-green-600"}
        />
      </div>

      {/* Second row stats */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Evaluations Run"
          value={summary.risk_posture.total_evaluations}
          subtitle="Total eval runs completed"
          icon={FlaskConical}
          color="bg-emerald-600"
        />
        <StatCard
          title="Avg Pass Rate"
          value={summary.risk_posture.avg_eval_pass_rate ? `${(summary.risk_posture.avg_eval_pass_rate * 100).toFixed(1)}%` : "N/A"}
          subtitle="Across all evaluation types"
          icon={TrendingUp}
          color="bg-teal-600"
        />
        <StatCard
          title="Compliance Frameworks"
          value={summary.compliance.frameworks.length}
          subtitle="Active framework mappings"
          icon={Shield}
          color="bg-slate-700"
        />
        <StatCard
          title="Evidence Artifacts"
          value="156"
          subtitle="Immutable, content-addressed"
          icon={FileCheck2}
          color="bg-amber-600"
        />
      </div>

      {/* Breakdowns */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <StatusBreakdown title="Models by Status" data={summary.inventory.models.by_status} />
        <StatusBreakdown title="Tools by Status" data={summary.inventory.tools.by_status} />
        <StatusBreakdown title="Use Cases by Risk" data={summary.inventory.use_cases.by_risk} />
      </div>

      {/* Compliance frameworks */}
      <div className="rounded-xl border bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Active Compliance Framework Mappings</h3>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-4">
          {summary.compliance.frameworks.map((fw) => (
            <div key={fw} className="flex items-center gap-2 rounded-lg border border-gray-100 bg-gray-50 p-3">
              <Shield className="h-4 w-4 text-green-600" />
              <span className="text-sm text-gray-700">{fw}</span>
            </div>
          ))}
        </div>
      </div>

      {/* PDCA Lifecycle */}
      <div className="rounded-xl border bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">ISO/IEC 42001 AIMS Lifecycle (PDCA)</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          {[
            { phase: "Plan", desc: "Use-case intake, risk assessment, policy definition", count: 2, color: "bg-blue-100 border-blue-300" },
            { phase: "Do", desc: "Build, test, evaluate, red-team", count: 3, color: "bg-green-100 border-green-300" },
            { phase: "Check", desc: "Monitoring, audits, canaries, drift detection", count: 1, color: "bg-yellow-100 border-yellow-300" },
            { phase: "Act", desc: "Remediation, recertification, continuous improvement", count: 2, color: "bg-purple-100 border-purple-300" },
          ].map((item) => (
            <div key={item.phase} className={cn("rounded-lg border-2 p-4", item.color)}>
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-lg font-bold text-gray-900">{item.phase}</h4>
                <span className="text-2xl font-bold text-gray-700">{item.count}</span>
              </div>
              <p className="text-xs text-gray-600">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
