"""
ClusterSeven IMS integration – EUC/tool inventory synchronization.

Morgan Stanley publicly uses ClusterSeven for inventorying and managing
End-User Computing (EUC) tools. This adapter syncs the Control Tower's
Tool registry with ClusterSeven IMS for:
  - Bidirectional inventory sync (tool registration, attestation status)
  - Attestation workflow triggering
  - Risk classification alignment
  - Committee reporting data export
"""

from __future__ import annotations

import httpx
import structlog

from app.integrations.base import BaseIntegration, IntegrationError

logger = structlog.get_logger()


class ClusterSevenAdapter(BaseIntegration):
    """Adapter for ClusterSeven IMS REST API."""

    def __init__(
        self,
        base_url: str = "",
        api_key: str = "",
    ) -> None:
        super().__init__("clusterseven")
        self.base_url = base_url.rstrip("/")
        self._api_key = api_key

    def _headers(self) -> dict:
        return {
            "Authorization": f"ApiKey {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def health_check(self) -> dict:
        self._check_circuit()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/api/v1/health", headers=self._headers())
                resp.raise_for_status()
                self._circuit.record_success()
                return {"status": "connected"}
        except Exception as e:
            self._circuit.record_failure()
            return {"status": "unreachable", "error": str(e)}

    async def sync_tool_to_ims(
        self,
        tool_id: str,
        name: str,
        category: str,
        criticality: str,
        owner: str,
        business_unit: str,
        location_path: str = "",
        attestation_status: str = "pending",
    ) -> dict:
        """Register or update a tool in ClusterSeven IMS."""
        self._check_circuit()
        payload = {
            "externalId": tool_id,
            "name": name,
            "classification": _map_category_to_ims(category),
            "riskLevel": _map_criticality_to_ims(criticality),
            "owner": owner,
            "businessUnit": business_unit,
            "filePath": location_path,
            "attestationStatus": attestation_status,
            "source": "ControlTower",
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.put(
                    f"{self.base_url}/api/v1/items/{tool_id}",
                    json=payload,
                    headers=self._headers(),
                )
                resp.raise_for_status()
                self._circuit.record_success()
                logger.info("clusterseven_tool_synced", tool_id=tool_id, name=name)
                return resp.json()
        except Exception as e:
            self._circuit.record_failure()
            raise IntegrationError("clusterseven", "sync_tool", str(e))

    async def get_tool_from_ims(self, external_id: str) -> dict | None:
        """Fetch a tool's current IMS record."""
        self._check_circuit()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.base_url}/api/v1/items/{external_id}",
                    headers=self._headers(),
                )
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
                self._circuit.record_success()
                return resp.json()
        except Exception as e:
            self._circuit.record_failure()
            raise IntegrationError("clusterseven", "get_tool", str(e))

    async def trigger_attestation(self, external_id: str, attestor_email: str) -> dict:
        """Trigger an attestation workflow in ClusterSeven."""
        self._check_circuit()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/v1/items/{external_id}/attest",
                    json={"attestor": attestor_email, "source": "ControlTower"},
                    headers=self._headers(),
                )
                resp.raise_for_status()
                self._circuit.record_success()
                return resp.json()
        except Exception as e:
            self._circuit.record_failure()
            raise IntegrationError("clusterseven", "trigger_attestation", str(e))

    async def export_inventory(self, business_unit: str | None = None) -> list[dict]:
        """Export full EUC inventory for committee reporting."""
        self._check_circuit()
        params = {}
        if business_unit:
            params["businessUnit"] = business_unit
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{self.base_url}/api/v1/items",
                    params=params,
                    headers=self._headers(),
                )
                resp.raise_for_status()
                self._circuit.record_success()
                return resp.json().get("items", [])
        except Exception as e:
            self._circuit.record_failure()
            raise IntegrationError("clusterseven", "export_inventory", str(e))


def _map_category_to_ims(category: str) -> str:
    mapping = {
        "euc_spreadsheet": "Spreadsheet",
        "euc_vba": "VBA Macro",
        "system_calculator": "System Calculator",
        "script": "Script",
        "dashboard": "Dashboard/Report",
        "api_service": "API Service",
        "agent_tool": "AI Agent Tool",
        "database_query": "Database Query",
    }
    return mapping.get(category, "Other")


def _map_criticality_to_ims(criticality: str) -> str:
    mapping = {"critical": "High", "high": "High", "medium": "Medium", "low": "Low"}
    return mapping.get(criticality, "Medium")
