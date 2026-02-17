"use client";

import { Settings, Shield, Database, Workflow, Eye, Bell } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-sm text-gray-500 mt-1">Control Tower system configuration</p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Policy Engine */}
        <div className="rounded-xl border bg-white p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <Shield className="h-5 w-5 text-primary" />
            <h3 className="text-sm font-semibold text-gray-900">Policy Engine (OPA)</h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">OPA Status</span>
              <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">Connected</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Active Policies</span>
              <span className="text-sm font-medium text-gray-900">4</span>
            </div>
            <div className="text-xs text-gray-500 mt-2 space-y-1">
              <p>• approval_gates.rego</p>
              <p>• data_classification.rego</p>
              <p>• agent_controls.rego</p>
              <p>• tool_permissions.rego</p>
            </div>
          </div>
        </div>

        {/* Workflow Engine */}
        <div className="rounded-xl border bg-white p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <Workflow className="h-5 w-5 text-primary" />
            <h3 className="text-sm font-semibold text-gray-900">Workflow Engine (Temporal)</h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Temporal Status</span>
              <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">Connected</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Namespace</span>
              <span className="text-sm font-medium text-gray-900">control-tower</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Task Queue</span>
              <span className="text-sm font-medium text-gray-900">ct-governance</span>
            </div>
          </div>
        </div>

        {/* Evidence Store */}
        <div className="rounded-xl border bg-white p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <Database className="h-5 w-5 text-primary" />
            <h3 className="text-sm font-semibold text-gray-900">Evidence Store (MinIO/S3)</h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Storage Status</span>
              <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">Connected</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Hashing Algorithm</span>
              <span className="text-sm font-medium text-gray-900">SHA-256</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Immutability (Object Lock)</span>
              <span className="text-sm font-medium text-gray-900">Enabled</span>
            </div>
          </div>
        </div>

        {/* Observability */}
        <div className="rounded-xl border bg-white p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <Eye className="h-5 w-5 text-primary" />
            <h3 className="text-sm font-semibold text-gray-900">Observability</h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">OpenTelemetry</span>
              <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">Active</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">LLM Tracing (Phoenix)</span>
              <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">Active</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Prometheus Metrics</span>
              <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">Active</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
