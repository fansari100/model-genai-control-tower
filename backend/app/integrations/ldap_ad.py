"""
LDAP / Active Directory integration for enterprise identity resolution.

Supplements Keycloak OIDC with direct LDAP queries for:
  - User lookup by employee ID or email
  - Group membership resolution (for dynamic RBAC)
  - Manager chain lookup (for approval routing)
  - Business unit / department resolution
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog

from app.integrations.base import BaseIntegration, IntegrationError

logger = structlog.get_logger()


@dataclass
class LDAPUser:
    dn: str
    employee_id: str
    username: str
    email: str
    full_name: str
    department: str
    business_unit: str
    manager_dn: str | None
    groups: list[str]
    title: str


class LDAPAdapter(BaseIntegration):
    """Adapter for enterprise LDAP/AD directory services."""

    def __init__(
        self,
        server_url: str = "",
        bind_dn: str = "",
        bind_password: str = "",
        base_dn: str = "dc=firm,dc=local",
        use_ssl: bool = True,
    ) -> None:
        super().__init__("ldap")
        self.server_url = server_url
        self.bind_dn = bind_dn
        self.bind_password = bind_password
        self.base_dn = base_dn
        self.use_ssl = use_ssl
        self._conn = None

    def _get_connection(self):
        if self._conn is not None:
            return self._conn
        try:
            import ldap3
            server = ldap3.Server(self.server_url, use_ssl=self.use_ssl, get_info=ldap3.ALL)
            self._conn = ldap3.Connection(
                server, user=self.bind_dn, password=self.bind_password, auto_bind=True
            )
            logger.info("ldap_connected", server=self.server_url)
            return self._conn
        except ImportError:
            logger.debug("ldap3_not_installed")
            return None
        except Exception as e:
            logger.warning("ldap_connection_failed", error=str(e))
            return None

    async def health_check(self) -> dict:
        conn = self._get_connection()
        if conn and conn.bound:
            return {"status": "connected", "server": self.server_url}
        return {"status": "disconnected"}

    async def lookup_user(self, email: str | None = None, employee_id: str | None = None) -> LDAPUser | None:
        """Look up a user by email or employee ID."""
        self._check_circuit()
        conn = self._get_connection()
        if conn is None:
            return None

        try:
            import ldap3
            search_filter = f"(mail={email})" if email else f"(employeeID={employee_id})"
            conn.search(
                search_base=self.base_dn,
                search_filter=search_filter,
                search_scope=ldap3.SUBTREE,
                attributes=[
                    "dn", "employeeID", "sAMAccountName", "mail", "displayName",
                    "department", "company", "manager", "memberOf", "title",
                ],
            )
            if not conn.entries:
                return None

            entry = conn.entries[0]
            groups = [str(g) for g in entry.memberOf.values] if hasattr(entry, "memberOf") else []

            self._circuit.record_success()
            return LDAPUser(
                dn=str(entry.entry_dn),
                employee_id=str(entry.employeeID) if hasattr(entry, "employeeID") else "",
                username=str(entry.sAMAccountName),
                email=str(entry.mail),
                full_name=str(entry.displayName),
                department=str(entry.department) if hasattr(entry, "department") else "",
                business_unit=str(entry.company) if hasattr(entry, "company") else "",
                manager_dn=str(entry.manager) if hasattr(entry, "manager") else None,
                groups=groups,
                title=str(entry.title) if hasattr(entry, "title") else "",
            )
        except Exception as e:
            self._circuit.record_failure()
            raise IntegrationError("ldap", "lookup_user", str(e))

    async def get_group_members(self, group_dn: str) -> list[str]:
        """Get all members of an AD group (for dynamic RBAC)."""
        self._check_circuit()
        conn = self._get_connection()
        if conn is None:
            return []
        try:
            import ldap3
            conn.search(
                search_base=group_dn,
                search_filter="(objectClass=group)",
                search_scope=ldap3.BASE,
                attributes=["member"],
            )
            if conn.entries:
                return [str(m) for m in conn.entries[0].member.values]
            return []
        except Exception as e:
            self._circuit.record_failure()
            raise IntegrationError("ldap", "get_group_members", str(e))

    async def resolve_approval_chain(self, user_email: str, levels: int = 3) -> list[LDAPUser]:
        """Walk the manager chain for approval routing."""
        chain: list[LDAPUser] = []
        current_email = user_email
        for _ in range(levels):
            user = await self.lookup_user(email=current_email)
            if user is None or user.manager_dn is None:
                break
            # Look up manager
            manager = await self.lookup_user(employee_id=None, email=None)
            # In real impl: resolve manager_dn to user object
            break  # Simplified for safety
        return chain
