"""API endpoint tests for Control Tower."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health endpoint returns ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    """Test root endpoint returns service info."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Control Tower" in data["service"]


@pytest.mark.asyncio
async def test_list_vendors_empty(client: AsyncClient):
    """Test listing vendors when empty."""
    response = await client.get("/api/v1/vendors")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_create_vendor(client: AsyncClient):
    """Test creating a vendor."""
    payload = {
        "name": "Test Vendor",
        "description": "A test vendor",
        "security_posture": "under_review",
    }
    response = await client.post("/api/v1/vendors", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Vendor"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_models_empty(client: AsyncClient):
    """Test listing models when empty."""
    response = await client.get("/api/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_model(client: AsyncClient):
    """Test creating a model."""
    payload = {
        "name": "Test LLM",
        "model_type": "llm",
        "owner": "Test Team",
        "version": "1.0",
    }
    response = await client.post("/api/v1/models", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test LLM"
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_list_tools_empty(client: AsyncClient):
    """Test listing tools when empty."""
    response = await client.get("/api/v1/tools")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_tool(client: AsyncClient):
    """Test creating a tool."""
    payload = {
        "name": "Test Calculator",
        "category": "euc_spreadsheet",
        "owner": "Test Ops",
        "criticality": "medium",
    }
    response = await client.post("/api/v1/tools", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Calculator"
    assert data["status"] == "under_review"


@pytest.mark.asyncio
async def test_list_use_cases_empty(client: AsyncClient):
    """Test listing use cases when empty."""
    response = await client.get("/api/v1/use-cases")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_intake_use_case(client: AsyncClient):
    """Test use case intake with risk rating computation."""
    payload = {
        "name": "Test GenAI App",
        "description": "A test GenAI application",
        "category": "rag_qa",
        "owner": "Test Team",
        "data_classification": "confidential",
        "handles_pii": True,
        "client_facing": True,
        "uses_rag": True,
        "uses_agents": True,
        "uses_tools": True,
        "uses_memory": True,
    }
    response = await client.post("/api/v1/use-cases/intake", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "risk_rating" in data
    assert "risk_score" in data
    assert "required_test_suites" in data
    assert len(data["required_test_suites"]) > 0
    assert data["risk_rating"] == "critical"  # All risk flags set → critical


@pytest.mark.asyncio
async def test_dashboard_summary(client: AsyncClient):
    """Test dashboard summary endpoint."""
    response = await client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "inventory" in data
    assert "risk_posture" in data
    assert "compliance" in data
