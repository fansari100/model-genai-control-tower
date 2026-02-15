"""
Generate a sample certification evidence pack (PDF + JSON).

Usage: cd backend && python -m scripts.generate_cert_pack
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.utils.pdf_generator import generate_certification_pack_pdf


def main() -> None:
    print("📦 Generating sample certification pack...")

    pack_data = {
        "pack_id": "CP-uc1-20260214",
        "use_case_id": "uc1",
        "use_case_name": "WM Assistant – Internal Q&A",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "risk_rating": "high",
        "overall_status": "approved",
        "sections": [
            {
                "section": "1_use_case_summary",
                "title": "Use Case Summary & Risk Assessment",
                "content": {
                    "name": "WM Assistant – Internal Q&A",
                    "description": "RAG-based Q&A assistant for WM advisors",
                    "category": "rag_qa",
                    "risk_rating": "high",
                    "data_classification": "confidential",
                    "client_facing": False,
                    "uses_agents": False,
                    "uses_rag": True,
                    "owner": "AI Platform Team",
                    "business_unit": "Wealth Management",
                },
            },
            {
                "section": "2_nist_genai_profile",
                "title": "NIST AI 600-1 GenAI Profile Compliance",
                "content": {
                    "governance": {"status": "compliant", "controls": 5},
                    "content_provenance": {"status": "compliant", "citation_required": True},
                    "pre_deployment_testing": {"status": "compliant", "test_suites": 6},
                    "incident_disclosure": {"status": "compliant", "escalation_path": "defined"},
                },
            },
            {
                "section": "3_owasp_mapping",
                "title": "OWASP LLM Top 10 & Agentic Top 10 Mapping",
                "content": {
                    "llm_risks_tested": ["LLM01", "LLM06", "LLM09"],
                    "agentic_risks_tested": [],
                    "coverage": "92%",
                },
            },
            {
                "section": "4_test_results",
                "title": "Pre-Deployment Testing Results",
                "content": {
                    "total_runs": 4,
                    "runs": [
                        {"type": "Quality", "tests": 50, "passed": 48, "pass_rate": 0.96},
                        {"type": "Red Team", "tests": 120, "passed": 115, "pass_rate": 0.958},
                        {"type": "RAG Eval", "tests": 30, "passed": 28, "pass_rate": 0.933},
                        {"type": "Controls", "tests": 5, "passed": 5, "pass_rate": 1.0},
                    ],
                },
            },
            {
                "section": "5_findings",
                "title": "Findings Register",
                "content": {
                    "total_findings": 3,
                    "findings": [
                        {"title": "Prompt injection bypass", "severity": "high", "status": "open"},
                        {"title": "PII in output", "severity": "critical", "status": "in_progress"},
                        {"title": "Outdated corpus docs", "severity": "low", "status": "open"},
                    ],
                },
            },
            {
                "section": "6_approvals",
                "title": "Governance Approval Record",
                "content": {
                    "approvals": [
                        {"gate": "Pre-Deployment", "decision": "Approved", "approver": "Jane Smith (MRO)"},
                    ],
                },
            },
            {
                "section": "7_monitoring",
                "title": "Ongoing Monitoring Plan",
                "content": {
                    "cadence": "daily",
                    "canary_count": 2,
                    "thresholds": {"faithfulness_min": 0.85, "toxicity_max": 0.05},
                },
            },
            {
                "section": "8_iso42001",
                "title": "ISO/IEC 42001 PDCA Mapping",
                "content": {
                    "phase": "Check",
                    "plan": "Completed",
                    "do": "Completed",
                    "check": "Active monitoring",
                    "act": "Continuous improvement",
                },
            },
        ],
        "summary": {
            "total_sections": 8,
            "open_critical_findings": 1,
            "certification_status": "approved",
            "generated_by": "Control Tower v1.0",
        },
    }

    # Generate PDF
    output_dir = Path(__file__).resolve().parent.parent / "eval" / "sample-data" / "cert-packs"
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_bytes = generate_certification_pack_pdf(pack_data)
    pdf_path = output_dir / "certification_pack_wm_assistant.pdf"
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)
    print(f"  ✅ PDF: {pdf_path} ({len(pdf_bytes)} bytes)")

    # Generate JSON
    json_path = output_dir / "certification_pack_wm_assistant.json"
    with open(json_path, "w") as f:
        json.dump(pack_data, f, indent=2, default=str)
    print(f"  ✅ JSON: {json_path}")

    print("\n📦 Certification pack generated!")


if __name__ == "__main__":
    main()
