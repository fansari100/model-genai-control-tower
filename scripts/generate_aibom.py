"""
Generate AI Bill of Materials (AIBOM) for registered models.

Usage: cd backend && python -m scripts.generate_aibom
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.services.aibom import generate_aibom, aibom_to_json


def main() -> None:
    print("📋 Generating AI Bills of Materials...")

    # GPT-5.2 AIBOM
    gpt52_aibom = generate_aibom(
        model_name="GPT-5.2",
        model_version="2024-11-20",
        model_type="llm",
        provider="OpenAI",
        provider_model_id="gpt-5.2-2025-12-11",
        deployment="vendor_api",
        context_window=128000,
        training_cutoff="2024-10",
        known_limitations="May hallucinate in specialized financial domains; not suitable for direct trade execution",
        dependencies=[
            {"name": "tiktoken", "version": "0.8.0"},
            {"name": "openai-python", "version": "1.58.0"},
        ],
        risk_tier="tier_2_high",
        licenses=["Proprietary"],
        additional_metadata={
            "sr_11_7_classification": "Model",
            "governance_status": "approved",
            "owasp_risks": "LLM01,LLM06,LLM09",
        },
    )

    # Claude Sonnet 5 AIBOM
    claude_aibom = generate_aibom(
        model_name="Claude Sonnet 5",
        model_version="20250514",
        model_type="llm",
        provider="Anthropic",
        provider_model_id="claude-sonnet-5-20260110",
        deployment="vendor_api",
        context_window=200000,
        training_cutoff="2025-04",
        known_limitations="Constitutional AI constraints may affect edge-case responses",
        dependencies=[
            {"name": "anthropic", "version": "0.40.0"},
        ],
        risk_tier="tier_2_high",
        licenses=["Proprietary"],
    )

    # Embeddings AIBOM
    embeddings_aibom = generate_aibom(
        model_name="text-embedding-3-large",
        model_version="1.0",
        model_type="deep_learning",
        provider="OpenAI",
        provider_model_id="text-embedding-3-large",
        deployment="vendor_api",
        risk_tier="tier_4_low",
        licenses=["Proprietary"],
    )

    # Save to files
    output_dir = Path(__file__).resolve().parent.parent / "eval" / "sample-data" / "aibom"
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, aibom in [
        ("gpt52", gpt52_aibom),
        ("claude_sonnet_5", claude_aibom),
        ("text_embedding_3_large", embeddings_aibom),
    ]:
        output_path = output_dir / f"aibom_{name}.json"
        with open(output_path, "w") as f:
            f.write(aibom_to_json(aibom))
        print(f"  ✅ Generated: {output_path}")

    print(f"\n📋 Generated {3} AIBOMs in {output_dir}")


if __name__ == "__main__":
    main()
