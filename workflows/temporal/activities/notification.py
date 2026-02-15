"""
Temporal activities for notifications.

Dispatches governance notifications to configured channels:
- Slack (webhook)
- Email (SMTP)
- Structured log (always, as fallback audit trail)
"""

from __future__ import annotations

import json
import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx
from temporalio import activity


async def _send_slack(message: str, channel_url: str | None = None) -> bool:
    """Post a message to Slack via incoming webhook."""
    webhook_url = channel_url or os.environ.get("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        activity.logger.debug("slack_skip_no_webhook")
        return False

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(webhook_url, json={"text": message})
            resp.raise_for_status()
            activity.logger.info("slack_sent", status=resp.status_code)
            return True
    except Exception as e:
        activity.logger.warning("slack_send_failed", error=str(e))
        return False


def _send_email(subject: str, body_html: str, recipients: list[str]) -> bool:
    """Send an email via SMTP."""
    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASSWORD", "")
    from_addr = os.environ.get("SMTP_FROM", "controltower@firm.local")

    if not smtp_host or not recipients:
        activity.logger.debug("email_skip_no_config")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = ", ".join(recipients)
        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if smtp_user:
                server.starttls()
                server.login(smtp_user, smtp_pass)
            server.sendmail(from_addr, recipients, msg.as_string())

        activity.logger.info("email_sent", recipients=recipients)
        return True
    except Exception as e:
        activity.logger.warning("email_send_failed", error=str(e))
        return False


@activity.defn(name="notify-approval-required")
async def notify_approval_required(
    use_case_id: str,
    required_approvers: list[str],
    eval_run_ids: list[str],
) -> dict:
    """Notify required approvers that a use case is ready for approval."""
    activity.logger.info(
        f"Notifying approvers for {use_case_id}: {required_approvers}"
    )

    message = (
        f"🔔 *Approval Required*\n"
        f"Use case `{use_case_id}` has completed {len(eval_run_ids)} evaluation runs "
        f"and requires approval.\n"
        f"Required approvers: {', '.join(required_approvers)}\n"
        f"Review at: /use-cases/{use_case_id}"
    )

    channels_used: list[str] = ["log"]
    slack_sent = await _send_slack(message)
    if slack_sent:
        channels_used.append("slack")

    email_sent = _send_email(
        subject=f"[Control Tower] Approval Required: {use_case_id}",
        body_html=f"<p>{message.replace(chr(10), '<br>')}</p>",
        recipients=[f"{a}@firm.local" for a in required_approvers],
    )
    if email_sent:
        channels_used.append("email")

    return {
        "notified": required_approvers,
        "use_case_id": use_case_id,
        "channels": channels_used,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@activity.defn(name="notify-certification-complete")
async def notify_certification_complete(
    use_case_id: str,
    status: str,
    evidence_pack_id: str,
) -> dict:
    """Notify stakeholders of certification completion."""
    activity.logger.info(
        f"Certification complete for {use_case_id}: {status}"
    )

    emoji = "✅" if status == "approved" else "⚠️" if status == "conditional" else "❌"
    message = (
        f"{emoji} *Certification {status.upper()}*\n"
        f"Use case: `{use_case_id}`\n"
        f"Evidence pack: `{evidence_pack_id}`\n"
        f"Download at: /certifications/{evidence_pack_id}"
    )

    channels_used: list[str] = ["log"]
    if await _send_slack(message):
        channels_used.append("slack")

    return {
        "use_case_id": use_case_id,
        "status": status,
        "evidence_pack_id": evidence_pack_id,
        "channels": channels_used,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@activity.defn(name="notify-recertification-triggered")
async def notify_recertification_triggered(
    use_case_id: str,
    trigger_reason: str,
) -> dict:
    """Notify that recertification has been triggered by a monitoring event."""
    activity.logger.info(
        f"Recertification triggered for {use_case_id}: {trigger_reason}"
    )

    message = (
        f"🔄 *Recertification Triggered*\n"
        f"Use case: `{use_case_id}`\n"
        f"Reason: {trigger_reason}\n"
        f"Action required: re-run certification pipeline."
    )

    channels_used: list[str] = ["log"]
    if await _send_slack(message):
        channels_used.append("slack")

    _send_email(
        subject=f"[Control Tower] RECERTIFICATION: {use_case_id}",
        body_html=f"<h3>Recertification Triggered</h3><p>Reason: {trigger_reason}</p>",
        recipients=[os.environ.get("MRO_EMAIL", "mro@firm.local")],
    )

    return {
        "use_case_id": use_case_id,
        "trigger_reason": trigger_reason,
        "channels": channels_used,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
