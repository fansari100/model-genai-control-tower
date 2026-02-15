"""
Salesforce CRM integration – meeting notes and action item sync.

Used by the Debrief meeting summarizer use case to:
  - Save structured meeting notes to Salesforce Activity objects
  - Create follow-up Tasks from action items
  - Link to client Contact/Account records
  - Enforce human-in-the-loop before write-back
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from app.integrations.base import BaseIntegration, IntegrationError

logger = structlog.get_logger()


class SalesforceAdapter(BaseIntegration):
    """Adapter for Salesforce REST API."""

    def __init__(
        self,
        instance_url: str = "",
        access_token: str = "",
        client_id: str = "",
        client_secret: str = "",
        api_version: str = "v60.0",
    ) -> None:
        super().__init__("salesforce")
        self.instance_url = instance_url.rstrip("/")
        self._access_token = access_token
        self._client_id = client_id
        self._client_secret = client_secret
        self.api_version = api_version

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    async def health_check(self) -> dict:
        self._check_circuit()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.instance_url}/services/data/{self.api_version}/limits",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                self._circuit.record_success()
                return {"status": "connected", "api_version": self.api_version}
        except Exception as e:
            self._circuit.record_failure()
            return {"status": "unreachable", "error": str(e)}

    async def create_activity(
        self,
        subject: str,
        description: str,
        contact_id: str,
        account_id: str,
        activity_date: str,
        meeting_notes: str,
        action_items: list[str],
    ) -> dict:
        """Save meeting notes as a Salesforce Event/Activity."""
        self._check_circuit()
        payload = {
            "Subject": subject,
            "Description": description,
            "WhoId": contact_id,
            "WhatId": account_id,
            "ActivityDate": activity_date,
            "Meeting_Notes__c": meeting_notes,
            "Action_Items__c": "\n".join(f"• {item}" for item in action_items),
            "Source__c": "Control Tower – Debrief",
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{self.instance_url}/services/data/{self.api_version}/sobjects/Event",
                    json=payload,
                    headers=self._headers(),
                )
                resp.raise_for_status()
                result = resp.json()
                self._circuit.record_success()
                logger.info("salesforce_activity_created", id=result.get("id"))
                return {"id": result["id"], "success": result.get("success", True)}
        except Exception as e:
            self._circuit.record_failure()
            raise IntegrationError("salesforce", "create_activity", str(e))

    async def create_task(
        self,
        subject: str,
        description: str,
        owner_id: str,
        due_date: str,
        priority: str = "Normal",
        related_to_id: str = "",
    ) -> dict:
        """Create a follow-up Task from a meeting action item."""
        self._check_circuit()
        payload = {
            "Subject": subject,
            "Description": description,
            "OwnerId": owner_id,
            "ActivityDate": due_date,
            "Priority": priority,
            "Status": "Not Started",
            "WhatId": related_to_id,
            "Source__c": "Control Tower – Debrief",
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{self.instance_url}/services/data/{self.api_version}/sobjects/Task",
                    json=payload,
                    headers=self._headers(),
                )
                resp.raise_for_status()
                result = resp.json()
                self._circuit.record_success()
                return {"id": result["id"], "success": True}
        except Exception as e:
            self._circuit.record_failure()
            raise IntegrationError("salesforce", "create_task", str(e))
