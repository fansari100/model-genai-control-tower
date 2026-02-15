"""Temporal worker – registers workflows and activities."""

from __future__ import annotations

import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from workflows.temporal.workflows.certification import CertificationWorkflow
from workflows.temporal.activities.evaluation import (
    run_quality_eval,
    run_security_eval,
    run_rag_eval,
    run_agentic_safety_eval,
    run_operational_controls_check,
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


async def main() -> None:
    """Start the Temporal worker."""
    client = await Client.connect("localhost:7233", namespace="control-tower")

    worker = Worker(
        client,
        task_queue="ct-governance",
        workflows=[CertificationWorkflow],
        activities=[
            run_quality_eval,
            run_security_eval,
            run_rag_eval,
            run_agentic_safety_eval,
            run_operational_controls_check,
            store_evidence_artifact,
            generate_certification_pack,
            notify_approval_required,
            notify_certification_complete,
            notify_recertification_triggered,
        ],
    )

    print("Temporal worker started on task queue: ct-governance")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
