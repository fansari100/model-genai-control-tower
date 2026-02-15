"use client";

import { Shield, CheckCircle2, AlertTriangle, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";

const owaspLlm = [
  { id: "LLM01", name: "Prompt Injection", controls: ["Cascade guardrail (regex → ML classifier)", "promptfoo 20+ injection tests", "PyRIT 10 attack scenarios", "OPA agent_controls.rego"], severity: "critical" },
  { id: "LLM02", name: "Insecure Output Handling", controls: ["Output guardrails: PII/toxicity scan", "HITL for client-facing outputs", "Output hash + evidence logging"], severity: "high" },
  { id: "LLM04", name: "Model DoS / Resource", controls: ["Token budget enforcement", "Rate limiting at gateway", "Cost tracking per eval run"], severity: "medium" },
  { id: "LLM06", name: "Sensitive Info Disclosure", controls: ["PII redaction (Presidio)", "OPA data_classification.rego", "Retrieval entitlement simulation"], severity: "critical" },
  { id: "LLM07", name: "Excessive Agency", controls: ["OPA tool_permissions.rego allowlists", "Per-turn tool call limits", "Human approval for write ops"], severity: "high" },
  { id: "LLM08", name: "Data & Model Poisoning", controls: ["AIBOM supply-chain transparency", "Dataset SHA-256 hashing", "Corpus change triggers recert"], severity: "high" },
  { id: "LLM09", name: "Misinformation", controls: ["RAG groundedness evaluation", "Mandatory citation enforcement", "Canary regression monitoring"], severity: "high" },
];

const owaspAgentic = [
  { id: "ASI01", name: "Agent Goal Hijack", controls: ["Immutable instruction prefix", "Goal drift evaluation suite", "Adversarial instruction tests (PyRIT)"] },
  { id: "ASI02", name: "Tool Misuse", controls: ["OPA tool_permissions.rego", "Argument schema validation", "Human approval for destructive ops"] },
  { id: "ASI03", name: "Identity/Privilege Abuse", controls: ["Scoped credentials per tool", "Keycloak service accounts", "Least-privilege OPA policy"] },
  { id: "ASI05", name: "Unexpected RCE", controls: ["OPA blocks eval/exec/subprocess patterns", "Sandboxed tool execution", "No dynamic code without approval"] },
  { id: "ASI06", name: "Memory/Context Poisoning", controls: ["Provenance required on memory writes", "TTL enforcement", "Write count limits (OPA: max 10)"] },
  { id: "ASI08", name: "Cascading Failures", controls: ["Temporal retry policies (max 3)", "Circuit breaker pattern", "Per-turn tool call limits (max 5)"] },
  { id: "ASI10", name: "Rogue Agents", controls: ["Agent registry with signed configs", "Kill switch (OPA check)", "Behavior anomaly monitoring"] },
];

const nistProfile = [
  { area: "Governance", controls: ["RBAC (6 Keycloak roles)", "OPA approval gates by risk tier", "Automated risk assessment + committee routing", "ISO 42001 PDCA lifecycle"] },
  { area: "Content Provenance", controls: ["Mandatory RAG citations", "Dataset SHA-256 + source tracking", "AIBOM (CycloneDX)", "Hash-chain evidence artifacts"] },
  { area: "Pre-deployment Testing", controls: ["3-layer eval: promptfoo + PyRIT + garak", "Risk-tier test suite requirements", "RAG groundedness (faithfulness, relevance)", "CI evaluation pipeline"] },
  { area: "Incident Disclosure", controls: ["Finding → Issue escalation", "Severity-based alert routing", "Immutable audit event stream", "NIST incident_disclosure field on use cases"] },
];

const sr117 = [
  { principle: "Model Definition", impl: "Model entity (type, purpose, I/O, limitations) + GenAI use case + Tool/EUC inventory" },
  { principle: "Effective Challenge", impl: "5-stage certification pipeline: intake → testing → approval → monitoring → recertification" },
  { principle: "Governance", impl: "Risk-tier committee paths + tamper-evident approval records + audit event stream" },
  { principle: "Ongoing Monitoring", impl: "Canary prompts + threshold drift alerts + automatic recertification triggers" },
];

const finra = [
  { requirement: "Prompt/Output Logging", impl: "Every eval captures input/output with PII redaction. Evidence artifacts store logs as content-addressed files." },
  { requirement: "Model Version Tracking", impl: "EvaluationRun records model_provider + model_version + prompt_template_hash." },
  { requirement: "Monitor Agentic AI", impl: "OWASP Agentic Top 10 2026 coverage, agent_controls.rego, kill switch, tool limits." },
];

function SevBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = { critical: "bg-red-100 text-red-800", high: "bg-orange-100 text-orange-800", medium: "bg-yellow-100 text-yellow-800" };
  return <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-semibold", colors[severity] || "bg-gray-100 text-gray-600")}>{severity.toUpperCase()}</span>;
}

export default function CompliancePage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Control Matrix</h1>
        <p className="text-sm text-gray-500 mt-1">Every risk mapped to a specific Control Tower control. This is the audit artifact.</p>
      </div>

      {/* OWASP LLM Top 10 2025 */}
      <section className="rounded-xl border bg-white p-6 shadow-sm">
        <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2"><Shield className="h-5 w-5 text-red-600" /> OWASP LLM Top 10 (2025)</h2>
        <div className="space-y-3">
          {owaspLlm.map((r) => (
            <div key={r.id} className="rounded-lg border border-gray-100 p-4">
              <div className="flex items-center gap-3 mb-2">
                <span className="font-mono text-xs font-bold text-gray-500 w-14">{r.id}</span>
                <span className="text-sm font-semibold text-gray-900 flex-1">{r.name}</span>
                <SevBadge severity={r.severity} />
              </div>
              <ul className="ml-[68px] space-y-1">
                {r.controls.map((c, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-gray-600">
                    <CheckCircle2 className="h-3.5 w-3.5 text-green-500 mt-0.5 flex-shrink-0" /> {c}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* OWASP Agentic Top 10 2026 */}
      <section className="rounded-xl border bg-white p-6 shadow-sm">
        <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2"><Shield className="h-5 w-5 text-purple-600" /> OWASP Agentic Top 10 (2026)</h2>
        <div className="space-y-3">
          {owaspAgentic.map((r) => (
            <div key={r.id} className="rounded-lg border border-gray-100 p-4">
              <div className="flex items-center gap-3 mb-2">
                <span className="font-mono text-xs font-bold text-gray-500 w-14">{r.id}</span>
                <span className="text-sm font-semibold text-gray-900">{r.name}</span>
              </div>
              <ul className="ml-[68px] space-y-1">
                {r.controls.map((c, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-gray-600">
                    <CheckCircle2 className="h-3.5 w-3.5 text-green-500 mt-0.5 flex-shrink-0" /> {c}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* NIST AI 600-1 */}
      <section className="rounded-xl border bg-white p-6 shadow-sm">
        <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2"><Shield className="h-5 w-5 text-blue-600" /> NIST AI 600-1 GenAI Profile</h2>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {nistProfile.map((n) => (
            <div key={n.area} className="rounded-lg border border-blue-100 bg-blue-50/30 p-4">
              <h3 className="text-sm font-bold text-blue-900 mb-2">{n.area}</h3>
              <ul className="space-y-1">
                {n.controls.map((c, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-gray-700">
                    <CheckCircle2 className="h-3.5 w-3.5 text-blue-500 mt-0.5 flex-shrink-0" /> {c}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* SR 11-7 */}
      <section className="rounded-xl border bg-white p-6 shadow-sm">
        <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2"><Shield className="h-5 w-5 text-slate-700" /> SR 11-7 / OCC Model Risk Management</h2>
        <div className="space-y-3">
          {sr117.map((s) => (
            <div key={s.principle} className="flex gap-4 rounded-lg border border-gray-100 p-4">
              <div className="w-40 flex-shrink-0">
                <span className="text-sm font-bold text-gray-900">{s.principle}</span>
              </div>
              <p className="text-xs text-gray-600 flex-1">{s.impl}</p>
            </div>
          ))}
        </div>
      </section>

      {/* FINRA */}
      <section className="rounded-xl border bg-white p-6 shadow-sm">
        <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2"><Shield className="h-5 w-5 text-emerald-600" /> FINRA GenAI Control Expectations</h2>
        <div className="space-y-3">
          {finra.map((f) => (
            <div key={f.requirement} className="flex gap-4 rounded-lg border border-gray-100 p-4">
              <div className="w-48 flex-shrink-0">
                <span className="text-sm font-bold text-gray-900">{f.requirement}</span>
              </div>
              <p className="text-xs text-gray-600 flex-1">{f.impl}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
