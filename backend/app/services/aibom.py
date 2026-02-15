"""
AIBOM (AI Bill of Materials) generator service.

Generates CycloneDX-aligned AI supply chain transparency documents.
This is the GenAI equivalent of SBOM (Software Bill of Materials).

Aligned with:
- OWASP AIBOM Generator concepts
- CycloneDX specification
- SPDX AI/ML profile
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import structlog

logger = structlog.get_logger()


def generate_aibom(
    model_name: str,
    model_version: str,
    model_type: str,
    provider: str | None = None,
    provider_model_id: str | None = None,
    deployment: str = "vendor_api",
    parameter_count: int | None = None,
    context_window: int | None = None,
    training_cutoff: str | None = None,
    known_limitations: str | None = None,
    dependencies: list[dict] | None = None,
    datasets: list[dict] | None = None,
    frameworks: list[dict] | None = None,
    licenses: list[str] | None = None,
    risk_tier: str | None = None,
    additional_metadata: dict | None = None,
) -> dict:
    """
    Generate an AIBOM (AI Bill of Materials) in CycloneDX-aligned format.

    Returns:
        A dictionary representing the AIBOM document.
    """
    now = datetime.now(timezone.utc)

    aibom: dict[str, Any] = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": f"urn:uuid:{_generate_bom_serial()}",
        "version": 1,
        "metadata": {
            "timestamp": now.isoformat(),
            "tools": [
                {
                    "vendor": "Control Tower",
                    "name": "CT-AIBOM-Generator",
                    "version": "1.0.0",
                }
            ],
            "component": {
                "type": "machine-learning-model",
                "name": model_name,
                "version": model_version,
            },
            "manufacture": {
                "name": provider or "Unknown",
            },
        },
        "components": [
            {
                "type": "machine-learning-model",
                "bom-ref": f"model-{model_name}-{model_version}",
                "name": model_name,
                "version": model_version,
                "description": f"{model_type} model",
                "properties": [
                    {"name": "ai:model:type", "value": model_type},
                    {"name": "ai:model:deployment", "value": deployment},
                    {"name": "ai:model:provider", "value": provider or "unknown"},
                    {"name": "ai:model:provider_id", "value": provider_model_id or "unknown"},
                ],
                "modelCard": {
                    "modelParameters": {
                        "approach": {"type": model_type},
                        "task": "general",
                    },
                    "quantitativeAnalysis": {},
                    "considerations": {
                        "technicalLimitations": [known_limitations] if known_limitations else [],
                    },
                },
            }
        ],
        "dependencies": [],
        "properties": [
            {"name": "ai:risk_tier", "value": risk_tier or "unclassified"},
            {"name": "ai:governance:framework", "value": "Control Tower v1.0"},
        ],
    }

    # Add model-specific properties
    if parameter_count:
        aibom["components"][0]["properties"].append(
            {"name": "ai:model:parameter_count", "value": str(parameter_count)}
        )
    if context_window:
        aibom["components"][0]["properties"].append(
            {"name": "ai:model:context_window", "value": str(context_window)}
        )
    if training_cutoff:
        aibom["components"][0]["properties"].append(
            {"name": "ai:model:training_cutoff", "value": training_cutoff}
        )

    # Add dependencies (libraries, frameworks)
    if dependencies:
        for dep in dependencies:
            aibom["components"].append({
                "type": "library",
                "bom-ref": f"dep-{dep.get('name', 'unknown')}",
                "name": dep.get("name", "unknown"),
                "version": dep.get("version", "unknown"),
            })
            aibom["dependencies"].append({
                "ref": f"model-{model_name}-{model_version}",
                "dependsOn": [f"dep-{dep.get('name', 'unknown')}"],
            })

    # Add training datasets
    if datasets:
        for ds in datasets:
            aibom["components"].append({
                "type": "data",
                "bom-ref": f"data-{ds.get('name', 'unknown')}",
                "name": ds.get("name", "unknown"),
                "description": ds.get("description", ""),
                "properties": [
                    {"name": "ai:data:type", "value": ds.get("type", "unknown")},
                    {"name": "ai:data:contains_pii", "value": str(ds.get("contains_pii", False))},
                ],
            })

    # Add frameworks
    if frameworks:
        for fw in frameworks:
            aibom["components"].append({
                "type": "framework",
                "bom-ref": f"fw-{fw.get('name', 'unknown')}",
                "name": fw.get("name", "unknown"),
                "version": fw.get("version", "unknown"),
            })

    # Add licenses
    if licenses:
        aibom["components"][0]["licenses"] = [
            {"license": {"id": lic}} for lic in licenses
        ]

    # Add additional metadata
    if additional_metadata:
        for key, value in additional_metadata.items():
            aibom["properties"].append({"name": f"ai:custom:{key}", "value": str(value)})

    logger.info(
        "aibom_generated",
        model=model_name,
        version=model_version,
        components=len(aibom["components"]),
    )

    return aibom


def _generate_bom_serial() -> str:
    """Generate a unique BOM serial number."""
    import uuid
    return str(uuid.uuid4())


def aibom_to_json(aibom: dict) -> str:
    """Serialize AIBOM to JSON string."""
    return json.dumps(aibom, indent=2, default=str)


def aibom_to_bytes(aibom: dict) -> bytes:
    """Serialize AIBOM to bytes for evidence storage."""
    return aibom_to_json(aibom).encode("utf-8")
