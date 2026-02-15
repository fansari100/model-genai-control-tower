"""Tests for the risk rating engine."""

from __future__ import annotations

from app.models.genai_use_case import DataClassification, RiskRating, UseCaseCategory
from app.services.risk_rating import compute_risk_rating


def test_minimal_risk():
    """Public, non-PII, non-client-facing → minimal/low risk."""
    result = compute_risk_rating(
        data_classification=DataClassification.PUBLIC,
        handles_pii=False,
        client_facing=False,
        uses_agents=False,
        uses_tools=False,
        uses_memory=False,
        uses_rag=False,
        category=UseCaseCategory.CLASSIFICATION,
    )
    assert result["risk_rating"] in [RiskRating.MINIMAL, RiskRating.LOW]
    assert result["risk_score"] < 50


def test_critical_risk():
    """PII + client-facing + agents + tools + memory → critical."""
    result = compute_risk_rating(
        data_classification=DataClassification.PII,
        handles_pii=True,
        client_facing=True,
        uses_agents=True,
        uses_tools=True,
        uses_memory=True,
        uses_rag=True,
        category=UseCaseCategory.AGENT_WORKFLOW,
    )
    assert result["risk_rating"] == RiskRating.CRITICAL
    assert result["risk_score"] >= 150
    assert len(result["required_test_suites"]) >= 7
    assert "agentic_safety" in result["required_test_suites"]


def test_owasp_agentic_risks_identified():
    """Agentic use case should identify OWASP Agentic Top 10 risks."""
    result = compute_risk_rating(
        data_classification=DataClassification.INTERNAL,
        handles_pii=False,
        client_facing=False,
        uses_agents=True,
        uses_tools=True,
        uses_memory=True,
        uses_rag=False,
        category=UseCaseCategory.AGENT_WORKFLOW,
    )
    assert len(result["owasp_agentic_risks"]) > 0
    assert "ASI01_Agent_Goal_Hijack" in result["owasp_agentic_risks"]
    assert "ASI02_Tool_Misuse" in result["owasp_agentic_risks"]
    assert "ASI06_Memory_Context_Poisoning" in result["owasp_agentic_risks"]


def test_nist_considerations_for_rag():
    """RAG use case should have content provenance considerations."""
    result = compute_risk_rating(
        data_classification=DataClassification.INTERNAL,
        handles_pii=False,
        client_facing=False,
        uses_agents=False,
        uses_tools=False,
        uses_memory=False,
        uses_rag=True,
        category=UseCaseCategory.RAG_QA,
    )
    nist = result["nist_considerations"]
    assert nist["content_provenance"]["applicable"] is True
    assert "citation_chain" in nist["content_provenance"]["controls"]


def test_committee_path_varies_by_risk():
    """Higher risk → more committee involvement."""
    low_result = compute_risk_rating(
        data_classification=DataClassification.PUBLIC,
        handles_pii=False,
        client_facing=False,
        uses_agents=False,
        uses_tools=False,
        uses_memory=False,
        uses_rag=False,
        category=UseCaseCategory.CLASSIFICATION,
    )
    high_result = compute_risk_rating(
        data_classification=DataClassification.PII,
        handles_pii=True,
        client_facing=True,
        uses_agents=True,
        uses_tools=True,
        uses_memory=True,
        uses_rag=True,
        category=UseCaseCategory.AGENT_WORKFLOW,
    )
    assert "Model Control Review" in low_result["committee_path"]
    assert "Enterprise Risk Committee" in high_result["committee_path"]
