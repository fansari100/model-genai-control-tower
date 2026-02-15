"""
Temporal workflow: Certification lifecycle.

Orchestrates the full certification pipeline:
  Intake → Testing → Approval (human signal) → Evidence Pack → Monitoring Setup

Each step is an activity that can be retried, timed out, and audited.
This is the core "effective challenge" workflow per SR 11-7.
"""

from __future__ import annotations

from datetime import timedelta
from dataclasses import dataclass, field

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from workflows.temporal.activities.evaluation import (
        run_quality_eval,
        run_security_eval,
        run_operational_controls_check,
        run_rag_eval,
        run_agentic_safety_eval,
    )
    from workflows.temporal.activities.evidence import (
        store_evidence_artifact,
        generate_certification_pack,
    )
    from workflows.temporal.activities.notification import (
        notify_approval_required,
        notify_certification_complete,
        notify_recertification_triggered,
    )


@dataclass
class CertificationInput:
    """Input for the certification workflow."""

    use_case_id: str
    risk_rating: str
    required_test_suites: list[str]
    required_approvals: list[str]
    owner: str
    initiated_by: str


@dataclass
class ApprovalSignal:
    """Signal sent by an approver to approve/reject."""

    decision: str  # "approved", "conditional", "rejected"
    approver: str
    rationale: str = ""
    conditions: list[str] = field(default_factory=list)


@dataclass
class CertificationResult:
    """Output of the certification workflow."""

    use_case_id: str
    status: str
    evidence_pack_id: str
    eval_run_ids: list[str]
    finding_count: int
    approval_ids: list[str]
    monitoring_plan_id: str | None


@workflow.defn(name="certification-workflow")
class CertificationWorkflow:
    """
    Full certification lifecycle workflow.
    Implements PDCA: Plan (intake) → Do (test) → Check (approve) → Act (monitor).
    """

    def __init__(self) -> None:
        self._approval_signals: list[ApprovalSignal] = []

    @workflow.signal
    async def submit_approval(self, signal: ApprovalSignal) -> None:
        """Signal handler: approver submits their decision."""
        self._approval_signals.append(signal)
        workflow.logger.info(f"Approval received from {signal.approver}: {signal.decision}")

    @workflow.run
    async def run(self, input: CertificationInput) -> CertificationResult:
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=3,
        )

        eval_run_ids: list[str] = []
        finding_count = 0

        # ── Stage 1: Pre-deployment Testing ──────────────────
        workflow.logger.info(f"Starting evaluations for {input.use_case_id}")

        if "quality_correctness" in input.required_test_suites:
            quality_result = await workflow.execute_activity(
                run_quality_eval,
                args=[input.use_case_id],
                start_to_close_timeout=timedelta(minutes=30),
                retry_policy=retry_policy,
            )
            eval_run_ids.append(quality_result["run_id"])
            finding_count += quality_result.get("findings", 0)

        if "rag_groundedness" in input.required_test_suites:
            rag_result = await workflow.execute_activity(
                run_rag_eval,
                args=[input.use_case_id],
                start_to_close_timeout=timedelta(minutes=30),
                retry_policy=retry_policy,
            )
            eval_run_ids.append(rag_result["run_id"])
            finding_count += rag_result.get("findings", 0)

        if "safety_security" in input.required_test_suites:
            security_result = await workflow.execute_activity(
                run_security_eval,
                args=[input.use_case_id],
                start_to_close_timeout=timedelta(minutes=60),
                retry_policy=retry_policy,
            )
            eval_run_ids.append(security_result["run_id"])
            finding_count += security_result.get("findings", 0)

        if "agentic_safety" in input.required_test_suites:
            agentic_result = await workflow.execute_activity(
                run_agentic_safety_eval,
                args=[input.use_case_id],
                start_to_close_timeout=timedelta(minutes=30),
                retry_policy=retry_policy,
            )
            eval_run_ids.append(agentic_result["run_id"])
            finding_count += agentic_result.get("findings", 0)

        if "operational_controls" in input.required_test_suites:
            controls_result = await workflow.execute_activity(
                run_operational_controls_check,
                args=[input.use_case_id],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=retry_policy,
            )
            eval_run_ids.append(controls_result["run_id"])
            finding_count += controls_result.get("findings", 0)

        # ── Stage 2: Approval Gate ───────────────────────────
        workflow.logger.info(
            f"Evaluations complete ({len(eval_run_ids)} runs, {finding_count} findings). "
            f"Requesting approval from: {input.required_approvals}"
        )

        await workflow.execute_activity(
            notify_approval_required,
            args=[input.use_case_id, input.required_approvals, eval_run_ids],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy,
        )

        # Wait for human approval via signal (with timeout based on risk tier)
        approval_timeout = {
            "critical": timedelta(days=14),
            "high": timedelta(days=10),
            "medium": timedelta(days=7),
            "low": timedelta(days=3),
            "minimal": timedelta(days=1),
        }.get(input.risk_rating, timedelta(days=7))

        try:
            await workflow.wait_condition(
                lambda: len(self._approval_signals) >= 1,
                timeout=approval_timeout,
            )
        except TimeoutError:
            workflow.logger.warning(
                f"Approval timeout after {approval_timeout} for {input.use_case_id}"
            )

        # Resolve final decision from collected signals
        approval_ids: list[str] = []
        final_decision = "pending"
        if self._approval_signals:
            last_signal = self._approval_signals[-1]
            final_decision = last_signal.decision
            approval_ids.append(f"approval-{last_signal.approver}")

        # ── Stage 3: Generate Certification Pack ─────────────
        pack_result = await workflow.execute_activity(
            generate_certification_pack,
            args=[input.use_case_id, eval_run_ids],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy,
        )
        evidence_pack_id = pack_result["pack_id"]

        # ── Determine final status ───────────────────────────
        if final_decision == "approved" and finding_count == 0:
            status = "approved"
        elif final_decision in ("approved", "conditional"):
            status = "conditional"
        elif final_decision == "rejected":
            status = "rejected"
        else:
            status = "conditional" if finding_count <= 3 else "rejected"

        # ── Notify completion ────────────────────────────────
        await workflow.execute_activity(
            notify_certification_complete,
            args=[input.use_case_id, status, evidence_pack_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy,
        )

        return CertificationResult(
            use_case_id=input.use_case_id,
            status=status,
            evidence_pack_id=evidence_pack_id,
            eval_run_ids=eval_run_ids,
            finding_count=finding_count,
            approval_ids=approval_ids,
            monitoring_plan_id=None,
        )
