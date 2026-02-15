"""
Audit event service – publishes immutable governance events to Kafka/Redpanda.

Every governance state change emits an event:
  UseCaseCreated, TestRunStarted, TestRunCompleted, ApprovalGranted,
  IssueOpened, FindingCreated, EvidenceStored, MonitoringAlertFired, etc.

These events form the append-only audit log required by SR 11-7 and FINRA.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import structlog

from app.config import get_settings
from app.utils.hashing import sha256_dict

logger = structlog.get_logger()


class AuditEventType(StrEnum):
    """Governance event taxonomy – every event is typed and versioned."""

    # Inventory
    VENDOR_CREATED = "vendor.created"
    VENDOR_UPDATED = "vendor.updated"
    MODEL_REGISTERED = "model.registered"
    MODEL_STATUS_CHANGED = "model.status_changed"
    TOOL_REGISTERED = "tool.registered"
    TOOL_ATTESTED = "tool.attested"

    # Use Case Lifecycle
    USE_CASE_INTAKE = "use_case.intake"
    USE_CASE_RISK_ASSESSED = "use_case.risk_assessed"
    USE_CASE_STATUS_CHANGED = "use_case.status_changed"

    # Evaluation
    EVAL_RUN_STARTED = "eval.run_started"
    EVAL_RUN_COMPLETED = "eval.run_completed"
    EVAL_RUN_FAILED = "eval.run_failed"

    # Security
    RED_TEAM_COMPLETED = "security.red_team_completed"
    VULNERABILITY_SCAN_COMPLETED = "security.vulnerability_scan_completed"
    GUARDRAIL_BLOCKED = "guardrail.blocked"
    GUARDRAIL_ESCALATED = "guardrail.escalated"

    # Findings
    FINDING_CREATED = "finding.created"
    FINDING_STATUS_CHANGED = "finding.status_changed"
    FINDING_REMEDIATED = "finding.remediated"

    # Approvals
    APPROVAL_GRANTED = "approval.granted"
    APPROVAL_REJECTED = "approval.rejected"
    APPROVAL_CONDITIONAL = "approval.conditional"

    # Evidence
    EVIDENCE_STORED = "evidence.stored"
    EVIDENCE_VERIFIED = "evidence.verified"
    CERTIFICATION_PACK_GENERATED = "certification.pack_generated"

    # Monitoring
    MONITORING_EXECUTION = "monitoring.execution"
    MONITORING_DRIFT_DETECTED = "monitoring.drift_detected"
    MONITORING_RECERT_TRIGGERED = "monitoring.recert_triggered"
    MONITORING_ALERT_FIRED = "monitoring.alert_fired"

    # Agent Controls
    AGENT_TOOL_BLOCKED = "agent.tool_blocked"
    AGENT_KILL_SWITCH = "agent.kill_switch"
    POLICY_VIOLATION = "policy.violation"


class AuditEvent:
    """An immutable, hashable governance event."""

    def __init__(
        self,
        event_type: AuditEventType,
        entity_type: str,
        entity_id: str,
        actor: str = "system",
        data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.event_type = event_type
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.actor = actor
        self.data = data or {}
        self.metadata = metadata or {}
        self.timestamp = datetime.now(UTC).isoformat()
        self.version = "1.0"

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "event_type": self.event_type.value,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "actor": self.actor,
            "timestamp": self.timestamp,
            "version": self.version,
            "data": self.data,
            "metadata": self.metadata,
        }
        payload["event_hash"] = sha256_dict(payload)
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str, sort_keys=True)


class AuditEventPublisher:
    """
    Publishes audit events to Kafka/Redpanda.
    Falls back to structured logging when Kafka is unavailable.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self._producer = None
        self._enabled = self.settings.enable_kafka

    async def _get_producer(self):
        """Lazy-init Kafka producer."""
        if self._producer is None and self._enabled:
            try:
                from aiokafka import AIOKafkaProducer

                self._producer = AIOKafkaProducer(
                    bootstrap_servers=self.settings.kafka_bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                    acks="all",  # Wait for all replicas → strong durability
                    enable_idempotence=True,
                )
                await self._producer.start()
                logger.info("kafka_producer_started", servers=self.settings.kafka_bootstrap_servers)
            except Exception as e:
                logger.warning("kafka_producer_init_failed", error=str(e))
                self._enabled = False
        return self._producer

    async def publish(self, event: AuditEvent) -> None:
        """Publish an audit event. Always logs; optionally sends to Kafka."""
        event_dict = event.to_dict()

        # Always log the event (structured logging = secondary audit trail)
        logger.info(
            "audit_event",
            event_type=event.event_type.value,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            actor=event.actor,
            event_hash=event_dict.get("event_hash", "")[:16],
        )

        # Publish to Kafka if enabled
        if self._enabled:
            producer = await self._get_producer()
            if producer:
                try:
                    topic = self.settings.kafka_topic_audit
                    await producer.send_and_wait(
                        topic,
                        value=event_dict,
                        key=event.entity_id.encode("utf-8"),
                    )
                except Exception as e:
                    logger.error(
                        "kafka_publish_failed", error=str(e), event_type=event.event_type.value
                    )

    async def close(self) -> None:
        """Gracefully shut down the producer."""
        if self._producer:
            await self._producer.stop()
            logger.info("kafka_producer_stopped")


# ── Singleton ────────────────────────────────────────────────
audit_publisher = AuditEventPublisher()


# ── Convenience helpers ──────────────────────────────────────


async def emit_use_case_intake(use_case_id: str, risk_rating: str, actor: str = "system") -> None:
    await audit_publisher.publish(
        AuditEvent(
            event_type=AuditEventType.USE_CASE_INTAKE,
            entity_type="genai_use_case",
            entity_id=use_case_id,
            actor=actor,
            data={"risk_rating": risk_rating},
        )
    )


async def emit_eval_completed(
    run_id: str, eval_type: str, pass_rate: float, use_case_id: str = ""
) -> None:
    await audit_publisher.publish(
        AuditEvent(
            event_type=AuditEventType.EVAL_RUN_COMPLETED,
            entity_type="evaluation_run",
            entity_id=run_id,
            data={"eval_type": eval_type, "pass_rate": pass_rate, "use_case_id": use_case_id},
        )
    )


async def emit_approval(
    approval_id: str, decision: str, gate_type: str, use_case_id: str, approver: str
) -> None:
    event_type = {
        "approved": AuditEventType.APPROVAL_GRANTED,
        "rejected": AuditEventType.APPROVAL_REJECTED,
        "conditional": AuditEventType.APPROVAL_CONDITIONAL,
    }.get(decision, AuditEventType.APPROVAL_GRANTED)

    await audit_publisher.publish(
        AuditEvent(
            event_type=event_type,
            entity_type="approval",
            entity_id=approval_id,
            actor=approver,
            data={"decision": decision, "gate_type": gate_type, "use_case_id": use_case_id},
        )
    )


async def emit_finding_created(
    finding_id: str, severity: str, source: str, owasp_risk_id: str | None = None
) -> None:
    await audit_publisher.publish(
        AuditEvent(
            event_type=AuditEventType.FINDING_CREATED,
            entity_type="finding",
            entity_id=finding_id,
            data={"severity": severity, "source": source, "owasp_risk_id": owasp_risk_id},
        )
    )


async def emit_guardrail_action(
    action: str, stage: str, reason: str, context: str = "input"
) -> None:
    event_type = (
        AuditEventType.GUARDRAIL_BLOCKED
        if action == "block"
        else AuditEventType.GUARDRAIL_ESCALATED
    )
    await audit_publisher.publish(
        AuditEvent(
            event_type=event_type,
            entity_type="guardrail",
            entity_id=stage,
            data={"action": action, "reason": reason, "context": context},
        )
    )


async def emit_evidence_stored(artifact_id: str, artifact_type: str, content_hash: str) -> None:
    await audit_publisher.publish(
        AuditEvent(
            event_type=AuditEventType.EVIDENCE_STORED,
            entity_type="evidence_artifact",
            entity_id=artifact_id,
            data={"artifact_type": artifact_type, "content_hash": content_hash[:16]},
        )
    )
