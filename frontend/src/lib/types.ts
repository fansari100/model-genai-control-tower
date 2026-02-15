// ─────────────────────────────────────────────────────────────
// Control Tower – TypeScript Type Definitions
// ─────────────────────────────────────────────────────────────

// ── Pagination ──────────────────────────────────────────────
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ── Vendor ──────────────────────────────────────────────────
export interface Vendor {
  id: string;
  name: string;
  legal_entity?: string;
  contract_id?: string;
  contact_email?: string;
  description?: string;
  security_posture: string;
  sla_summary?: string;
  data_processing_region?: string;
  certifications?: Record<string, boolean>;
  redteam_due_diligence?: Record<string, string>;
  created_at?: string;
  updated_at?: string;
}

// ── Model ───────────────────────────────────────────────────
export type ModelType = "statistical" | "ml_traditional" | "deep_learning" | "llm" | "multimodal" | "ensemble";
export type ModelStatus = "draft" | "intake" | "under_review" | "approved" | "conditional" | "deprecated" | "retired";
export type RiskTier = "tier_1_critical" | "tier_2_high" | "tier_3_medium" | "tier_4_low";

export interface Model {
  id: string;
  name: string;
  version: string;
  description?: string;
  purpose?: string;
  model_type: ModelType;
  deployment: string;
  status: ModelStatus;
  risk_tier: RiskTier;
  owner: string;
  business_unit?: string;
  vendor_id?: string;
  provider_model_id?: string;
  created_at?: string;
}

// ── Tool / EUC ──────────────────────────────────────────────
export type ToolCategory = "euc_spreadsheet" | "euc_vba" | "system_calculator" | "script" | "dashboard" | "api_service" | "agent_tool" | "database_query" | "other";
export type ToolCriticality = "critical" | "high" | "medium" | "low";
export type ToolStatus = "active" | "under_review" | "attested" | "attestation_due" | "attestation_overdue" | "deprecated" | "retired";

export interface Tool {
  id: string;
  name: string;
  version: string;
  description?: string;
  category: ToolCategory;
  criticality: ToolCriticality;
  status: ToolStatus;
  owner: string;
  last_attestation_date?: string;
  next_attestation_date?: string;
  created_at?: string;
}

// ── GenAI Use Case ──────────────────────────────────────────
export type UseCaseCategory = "rag_qa" | "summarization" | "content_generation" | "data_extraction" | "code_generation" | "agent_workflow" | "classification" | "translation" | "other";
export type UseCaseStatus = "draft" | "intake" | "risk_assessment" | "testing" | "pending_approval" | "approved" | "conditional" | "monitoring" | "recertification" | "suspended" | "retired";
export type RiskRating = "critical" | "high" | "medium" | "low" | "minimal";
export type DataClassification = "public" | "internal" | "confidential" | "pii" | "restricted";

export interface GenAIUseCase {
  id: string;
  name: string;
  version: string;
  description?: string;
  category: UseCaseCategory;
  status: UseCaseStatus;
  risk_rating: RiskRating;
  data_classification: DataClassification;
  client_facing: boolean;
  uses_agents: boolean;
  uses_rag: boolean;
  uses_tools: boolean;
  uses_memory: boolean;
  requires_human_in_loop: boolean;
  owner: string;
  business_unit?: string;
  required_test_suites?: string[];
  created_at?: string;
}

// ── Evaluation ──────────────────────────────────────────────
export type EvalType = "quality_correctness" | "safety_security" | "operational_controls" | "rag_groundedness" | "red_team_promptfoo" | "red_team_pyrit" | "vulnerability_garak" | "regression" | "canary" | "agentic_safety";
export type EvalStatus = "pending" | "running" | "completed" | "failed" | "cancelled";

export interface EvaluationRun {
  id: string;
  name: string;
  eval_type: EvalType;
  status: EvalStatus;
  use_case_id?: string;
  total_tests: number;
  passed: number;
  failed: number;
  pass_rate?: number;
  aggregate_scores?: Record<string, number>;
  owasp_category_results?: Record<string, any>;
  started_at?: string;
  completed_at?: string;
  created_at?: string;
}

// ── Finding ─────────────────────────────────────────────────
export type FindingSeverity = "critical" | "high" | "medium" | "low" | "informational";
export type FindingStatus = "open" | "in_progress" | "mitigated" | "accepted" | "closed" | "reopened";

export interface Finding {
  id: string;
  title: string;
  description?: string;
  severity: FindingSeverity;
  status: FindingStatus;
  source: string;
  use_case_id?: string;
  owasp_risk_id?: string;
  remediation_owner?: string;
  remediation_due_date?: string;
  created_at?: string;
}

// ── Approval ────────────────────────────────────────────────
export interface Approval {
  id: string;
  gate_type: string;
  decision: string;
  approver_role: string;
  approver_name: string;
  rationale?: string;
  conditions?: string[];
  decision_hash?: string;
  created_at?: string;
}

// ── Dashboard ───────────────────────────────────────────────
export interface DashboardSummary {
  inventory: {
    models: { total: number; by_status: Record<string, number> };
    tools: { total: number; by_status: Record<string, number> };
    use_cases: { total: number; by_status: Record<string, number>; by_risk: Record<string, number> };
  };
  risk_posture: {
    open_critical_findings: number;
    total_findings: number;
    avg_eval_pass_rate?: number;
    total_evaluations: number;
  };
  compliance: {
    frameworks: string[];
    status: string;
  };
}
