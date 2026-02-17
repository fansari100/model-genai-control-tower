"use client";

import { useState } from "react";

const demos = [
  {
    id: "doc-intel",
    name: "Document Intelligence",
    endpoint: "/api/v1/model-demos/document-intelligence/extract",
    inputLabel: "Paste financial document text (prospectus, fact sheet):",
    inputKey: "text",
    placeholder: `The Morgan Stanley Growth Fund (MSGFX) seeks long-term capital appreciation by investing primarily in growth-oriented equity securities.

The fund has an expense ratio of 0.85% and a front-end load of 5.25%.
As of December 2025, AUM is $4.2 billion.

Performance:
  1-year return: 18.3% vs S&P 500 at 16.2%
  3-year annualized: 12.1%
  5-year annualized: 14.7%

Risk Metrics:
  Sharpe Ratio: 1.24
  Standard Deviation: 15.8%
  Beta: 1.05

Top Holdings:
  AAPL (8.2%), MSFT (7.1%), NVDA (6.8%), AMZN (5.4%), GOOGL (4.9%)`,
  },
  {
    id: "meeting-sum",
    name: "Meeting Summarizer",
    endpoint: "/api/v1/model-demos/meeting-summarizer/summarize",
    inputLabel: "Paste meeting transcript:",
    inputKey: "transcript",
    placeholder: `Advisor: Good morning, Mr. Chen. Let's review your portfolio today.

Client: Thanks. I'm concerned about interest rate risk given the current environment.

Advisor: That's a valid concern. Your fixed income allocation is 30% with an average duration of 7 years. We could reduce duration to 3-4 years by shifting from long-term bonds to intermediate-term.

Client: What about the equity side?

Advisor: Given your 15-year horizon, I'd maintain the 60% equity weight but increase international exposure by 5%. Emerging markets look attractive at current valuations.

Client: Sounds reasonable. I also wanted to discuss the 529 plan for my daughter.

Advisor: Absolutely. Given she's 8, we have a 10-year horizon. I'd recommend the age-based portfolio option with a moderate risk profile.

Client: Great, let's proceed with all of that.`,
  },
  {
    id: "risk-narrator",
    name: "Portfolio Risk Narrator",
    endpoint: "/api/v1/model-demos/portfolio-risk-narrator/generate",
    inputLabel: "Portfolio data (JSON):",
    inputKey: "portfolio",
    placeholder: `{
  "client_name": "Smith Family Trust",
  "total_value": 10000000,
  "ytd_return_pct": 8.2,
  "volatility_pct": 14.2,
  "sharpe_ratio": 1.15,
  "max_drawdown_pct": -6.3,
  "allocation": {
    "us_equity": 45,
    "intl_equity": 15,
    "fixed_income": 25,
    "alternatives": 10,
    "cash": 5
  },
  "benchmark": "60/40 Blended",
  "benchmark_return_pct": 7.1
}`,
  },
  {
    id: "reg-detector",
    name: "Regulatory Change Detector",
    endpoint: "/api/v1/model-demos/regulatory-change-detector/analyze",
    inputLabel: "Paste regulatory document text:",
    inputKey: "text",
    placeholder: `FINRA Regulatory Notice 26-03
Effective Date: March 15, 2026

Subject: Supervision Requirements for Generative AI in Client Communications

Summary:
Firms that use generative AI tools to draft, review, or personalize client communications must implement the following supervision procedures:

1. All GenAI-generated content must be reviewed by a registered principal before distribution to retail clients.

2. Firms must maintain complete records of AI model versions, prompts, and outputs for a minimum of 3 years.

3. Firms must conduct periodic testing of GenAI outputs for compliance with FINRA Rule 2210 (Communications with the Public).

4. Any material changes to GenAI models or prompts used in client-facing communications require updated supervisory procedures within 30 days.

Failure to comply may result in enforcement action under FINRA Rules 3110 and 3120.`,
  },
  {
    id: "compliance-chk",
    name: "Compliance Checker",
    endpoint: "/api/v1/model-demos/compliance-checker/check",
    inputLabel: "Paste draft client communication:",
    inputKey: "text",
    placeholder: `Dear Mr. Johnson,

I'm pleased to share that our Growth Fund has guaranteed returns of 12% annually. This risk-free investment is perfect for your retirement portfolio.

The fund has outperformed the market every year for the past decade, delivering a 15.3% annual return. Based on our projections, your $500,000 investment will grow to $1.5 million within 5 years.

Your Social Security number (123-45-6789) has been updated in our records.

Best regards,
Financial Advisor`,
  },
];

/**
 * Strip markdown code fences that LLMs sometimes wrap around JSON.
 * e.g. ```json\n{...}\n``` → {...}
 */
function stripCodeFences(str: string): string {
  const trimmed = str.trim();
  const fenceMatch = trimmed.match(/^```(?:\w+)?\s*\n([\s\S]*?)\n```$/);
  return fenceMatch ? fenceMatch[1].trim() : trimmed;
}

/**
 * Try to parse a string as JSON, stripping code fences first.
 */
function tryParseJson(str: string): unknown | null {
  const cleaned = stripCodeFences(str);
  try {
    const parsed = JSON.parse(cleaned);
    if (typeof parsed === "object" && parsed !== null) return parsed;
  } catch { /* not JSON */ }
  return null;
}

/**
 * Recursively format output for human-readable display.
 * - Parses nested JSON strings (LLM often returns JSON inside a text field)
 * - Strips markdown code fences (```json ... ```)
 * - Preserves newlines in string values
 * - Indents nested structures cleanly
 */
function formatOutput(data: unknown, indent = 0): string {
  if (data === null || data === undefined) return "null";

  if (typeof data === "string") {
    const parsed = tryParseJson(data);
    if (parsed) return formatOutput(parsed, indent);
    return data;
  }

  if (typeof data === "number" || typeof data === "boolean") {
    return String(data);
  }

  const pad = "  ".repeat(indent + 1);
  const closePad = "  ".repeat(indent);

  if (Array.isArray(data)) {
    if (data.length === 0) return "[]";
    const items = data.map((item) => {
      if (typeof item === "object" && item !== null) {
        return `${pad}${formatOutput(item, indent + 1)}`;
      }
      if (typeof item === "string") return `${pad}${item}`;
      return `${pad}${JSON.stringify(item)}`;
    });
    return `[\n${items.join(",\n")}\n${closePad}]`;
  }

  if (typeof data === "object") {
    const entries = Object.entries(data as Record<string, unknown>);
    if (entries.length === 0) return "{}";
    const lines = entries.map(([key, value]) => {
      let formattedValue: string;

      if (typeof value === "string") {
        // Try parsing as nested JSON (with code-fence stripping)
        const nested = tryParseJson(value);
        if (nested) {
          formattedValue = formatOutput(nested, indent + 1);
        } else if (value.includes("\n")) {
          // Multi-line string: preserve newlines with indentation
          const valueLines = value.split("\n");
          formattedValue = valueLines
            .map((line, i) => (i === 0 ? line : `${pad}  ${line}`))
            .join("\n");
        } else {
          formattedValue = `"${value}"`;
        }
      } else if (typeof value === "object" && value !== null) {
        formattedValue = formatOutput(value, indent + 1);
      } else {
        formattedValue = JSON.stringify(value);
      }

      return `${pad}${key}: ${formattedValue}`;
    });
    return `{\n${lines.join("\n")}\n${closePad}}`;
  }

  return String(data);
}

export default function DemoPage() {
  const [activeDemo, setActiveDemo] = useState(demos[0]);
  const [input, setInput] = useState(activeDemo.placeholder);
  const [output, setOutput] = useState<unknown>(null);
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
      setOutput({ error: "API not running. Start backend: uvicorn app.main:app --port 8000" });
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
            className="w-full h-72 rounded-lg border p-3 text-sm font-mono leading-relaxed focus:outline-none focus:ring-2 focus:ring-primary"
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
          <pre className="w-full h-72 rounded-lg border bg-gray-50 p-3 text-xs font-mono leading-relaxed overflow-auto whitespace-pre-wrap break-words">
            {output ? formatOutput(output) : "Click 'Run Model' to see output"}
          </pre>
        </div>
      </div>
    </div>
  );
}
