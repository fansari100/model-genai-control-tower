"use client";

import { useState } from "react";

const demos = [
  {
    id: "doc-intel",
    name: "Document Intelligence",
    endpoint: "/api/v1/model-demos/document-intelligence/extract",
    inputLabel: "Paste financial document text (prospectus, fact sheet):",
    inputKey: "text",
    placeholder: "The Morgan Stanley Growth Fund (MSGFX) seeks long-term capital appreciation by investing primarily in growth-oriented equity securities. The fund has an expense ratio of 0.85% and a front-end load of 5.25%. As of December 2025, AUM is $4.2 billion. The fund's 1-year return is 18.3% vs S&P 500 at 16.2%. Top holdings include AAPL (8.2%), MSFT (7.1%), NVDA (6.8%)...",
  },
  {
    id: "meeting-sum",
    name: "Meeting Summarizer",
    endpoint: "/api/v1/model-demos/meeting-summarizer/summarize",
    inputLabel: "Paste meeting transcript:",
    inputKey: "transcript",
    placeholder: "Advisor: Good morning. Let's review your portfolio.\nClient: I'm concerned about interest rate risk.\nAdvisor: We could reduce duration in fixed income...",
  },
  {
    id: "risk-narrator",
    name: "Portfolio Risk Narrator",
    endpoint: "/api/v1/model-demos/portfolio-risk-narrator/generate",
    inputLabel: "Portfolio data (JSON):",
    inputKey: "portfolio",
    placeholder: '{"client_name": "Smith Family Trust", "total_value": 10000000, "ytd_return_pct": 8.2, "volatility_pct": 14.2, "sharpe_ratio": 1.15}',
  },
  {
    id: "reg-detector",
    name: "Regulatory Change Detector",
    endpoint: "/api/v1/model-demos/regulatory-change-detector/analyze",
    inputLabel: "Paste regulatory document text:",
    inputKey: "text",
    placeholder: "FINRA Regulatory Notice 26-03: Firms must implement supervision procedures for GenAI-generated client communications...",
  },
  {
    id: "compliance-chk",
    name: "Compliance Checker",
    endpoint: "/api/v1/model-demos/compliance-checker/check",
    inputLabel: "Paste draft client communication:",
    inputKey: "text",
    placeholder: "Dear Mr. Johnson, I'm pleased to share that our Growth Fund has guaranteed returns of 12% annually. This risk-free investment is perfect for your retirement portfolio...",
  },
];

export default function DemoPage() {
  const [activeDemo, setActiveDemo] = useState(demos[0]);
  const [input, setInput] = useState(activeDemo.placeholder);
  const [output, setOutput] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const runDemo = async () => {
    setLoading(true);
    try {
      const res = await fetch(activeDemo.endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ [activeDemo.inputKey]: input }),
      });
      const data = await res.json();
      setOutput(data);
    } catch {
      setOutput({ error: "API not running. Start backend: uvicorn governance.app.main:app --port 8000" });
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Live Model Demo</h1>
        <p className="text-sm text-gray-500">Interact with all 5 GenAI models in real-time</p>
      </div>

      <div className="flex gap-2 flex-wrap">
        {demos.map(d => (
          <button
            key={d.id}
            onClick={() => { setActiveDemo(d); setInput(d.placeholder); setOutput(null); }}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
              activeDemo.id === d.id ? "bg-primary text-white" : "bg-white border text-gray-700 hover:bg-gray-50"
            }`}
          >
            {d.name}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-3">
          <label className="text-sm font-medium text-gray-700">{activeDemo.inputLabel}</label>
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            className="w-full h-64 rounded-lg border p-3 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <button
            onClick={runDemo}
            disabled={loading}
            className="rounded-lg bg-primary px-6 py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:opacity-50"
          >
            {loading ? "Processing..." : "Run Model"}
          </button>
        </div>

        <div className="space-y-3">
          <label className="text-sm font-medium text-gray-700">Model Output:</label>
          <pre className="w-full h-64 rounded-lg border bg-gray-50 p-3 text-xs font-mono overflow-auto">
            {output ? JSON.stringify(output, null, 2) : "Click 'Run Model' to see output"}
          </pre>
        </div>
      </div>
    </div>
  );
}
