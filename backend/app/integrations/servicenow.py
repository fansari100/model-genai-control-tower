"""
ServiceNow integration – issue tracking and change management.

Maps Control Tower Issues/Findings to ServiceNow Incidents and Change Requests.
Used for: finding escalation, remediation tracking, CAB approval integration.
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from app.integrations.base import BaseIntegration, IntegrationError

logger = structlog.get_logger()


class ServiceNowAdapter(BaseIntegration):
    """Adapter for ServiceNow REST API (Table API + CMDB)."""

    def __init__(
        self,
        instance_url: str = "",
        username: str = "",
        password: str = "",
    ) -> None:
        super().__init__("servicenow")
        self.instance_url = instance_url.rstrip("/")
        self._auth = (username, password) if username else None

    async def health_check(self) -> dict:
        self._check_circuit()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.instance_url}/api/now/table/sys_properties?sysparm_limit=1",
                    auth=self._auth,
                )
                resp.raise_for_status()
                self._circuit.record_success()
                return {"status": "connected", "instance": self.instance_url}
        except Exception as e:
            self._circuit.record_failure()
            return {"status": "unreachable", "error": str(e)}

    async def create_incident(
        self,
        short_description: str,
        description: str,
        severity: int = 3,
        assignment_group: str = "Model Control",
        caller_id: str = "control-tower",
        custom_fields: dict | None = None,
    ) -> dict:
        """Create a ServiceNow incident from a Control Tower finding."""
        self._check_circuit()
        payload: dict[str, Any] = {
            "short_description": short_description,
            "description": description,
            "severity": severity,
            "urgency": min(severity, 3),
            "impact": min(severity, 3),
            "assignment_group": assignment_group,
            "caller_id": caller_id,
            "category": "AI/ML Model Risk",
        }
        if custom_fields:
            payload.update(custom_fields)

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{self.instance_url}/api/now/table/incident",
                    json=payload,
                    auth=self._auth,
                    headers={"Content-Type": "application/json", "Accept": "application/json"},
                )
                resp.raise_for_status()
                result = resp.json()["result"]
                self._circuit.record_success()
                logger.info("servicenow_incident_created", number=result.get("number"))
                return {"sys_id": result["sys_id"], "number": result["number"]}
        except Exception as e:
            self._circuit.record_failure()
            raise IntegrationError("servicenow", "create_incident", str(e))

    async def create_change_request(
        self,
        short_description: str,
        description: str,
        change_type: str = "normal",
        risk: str = "moderate",
    ) -> dict:
        """Create a change request (for CAB approval of production deployments)."""
        self._check_circuit()
        payload = {
            "short_description": short_description,
            "description": description,
            "type": change_type,
            "risk": risk,
            "category": "AI/ML Governance",
            "assignment_group": "Model Control",
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{self.instance_url}/api/now/table/change_request",
                    json=payload,
                    auth=self._auth,
                    headers={"Content-Type": "application/json", "Accept": "application/json"},
                )
                resp.raise_for_status()
                result = resp.json()["result"]
                self._circuit.record_success()
                return {"sys_id": result["sys_id"], "number": result["number"]}
        except Exception as e:
            self._circuit.record_failure()
            raise IntegrationError("servicenow", "create_change_request", str(e))

    async def update_incident_status(self, sys_id: str, state: int, notes: str = "") -> dict:
        """Update incident state (1=New, 2=InProgress, 6=Resolved, 7=Closed)."""
        self._check_circuit()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.patch(
                    f"{self.instance_url}/api/now/table/incident/{sys_id}",
                    json={"state": state, "work_notes": notes},
                    auth=self._auth,
                )
                resp.raise_for_status()
                self._circuit.record_success()
                return resp.json().get("result", {})
        except Exception as e:
            self._circuit.record_failure()
            raise IntegrationError("servicenow", "update_incident", str(e))
