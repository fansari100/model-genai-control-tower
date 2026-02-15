import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | undefined): string {
  if (!date) return "—";
  return new Date(date).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatDateTime(date: string | undefined): string {
  if (!date) return "—";
  return new Date(date).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function statusColor(status: string): string {
  const colors: Record<string, string> = {
    approved: "bg-green-100 text-green-800",
    active: "bg-green-100 text-green-800",
    attested: "bg-green-100 text-green-800",
    completed: "bg-green-100 text-green-800",
    closed: "bg-green-100 text-green-800",
    monitoring: "bg-blue-100 text-blue-800",
    running: "bg-blue-100 text-blue-800",
    in_progress: "bg-blue-100 text-blue-800",
    testing: "bg-blue-100 text-blue-800",
    pending: "bg-yellow-100 text-yellow-800",
    pending_approval: "bg-yellow-100 text-yellow-800",
    draft: "bg-gray-100 text-gray-800",
    under_review: "bg-purple-100 text-purple-800",
    risk_assessment: "bg-purple-100 text-purple-800",
    intake: "bg-indigo-100 text-indigo-800",
    conditional: "bg-orange-100 text-orange-800",
    attestation_due: "bg-orange-100 text-orange-800",
    suspended: "bg-red-100 text-red-800",
    rejected: "bg-red-100 text-red-800",
    failed: "bg-red-100 text-red-800",
    retired: "bg-gray-100 text-gray-500",
    deprecated: "bg-gray-100 text-gray-500",
    attestation_overdue: "bg-red-100 text-red-800",
    open: "bg-red-100 text-red-800",
    mitigated: "bg-green-100 text-green-800",
  };
  return colors[status] || "bg-gray-100 text-gray-800";
}

export function severityColor(severity: string): string {
  const colors: Record<string, string> = {
    critical: "bg-red-600 text-white",
    high: "bg-red-100 text-red-800",
    medium: "bg-yellow-100 text-yellow-800",
    low: "bg-blue-100 text-blue-800",
    minimal: "bg-gray-100 text-gray-600",
    informational: "bg-gray-100 text-gray-600",
  };
  return colors[severity] || "bg-gray-100 text-gray-800";
}

export function riskColor(risk: string): string {
  const colors: Record<string, string> = {
    critical: "bg-red-600 text-white",
    high: "bg-red-100 text-red-800",
    medium: "bg-yellow-100 text-yellow-800",
    low: "bg-green-100 text-green-800",
    minimal: "bg-gray-100 text-gray-600",
    tier_1_critical: "bg-red-600 text-white",
    tier_2_high: "bg-red-100 text-red-800",
    tier_3_medium: "bg-yellow-100 text-yellow-800",
    tier_4_low: "bg-green-100 text-green-800",
  };
  return colors[risk] || "bg-gray-100 text-gray-800";
}

export function humanize(str: string): string {
  return str
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
