"""
Client Communication Compliance Checker — GenAI Model #5

Pre-send compliance screening for advisor-drafted client communications
(emails, letters, proposals). Checks for:
  - Misleading performance claims
  - Missing required disclosures
  - Unsuitable product recommendations
  - Promissory language ("guaranteed", "risk-free")
  - Regulatory violation indicators
  - PII that shouldn't be in external communications

Architecture:
  - Input: Draft communication text + client context
  - Processing: LLM classification + NER + rule-based checks
  - Output: Pass/Fail decision with specific violations and fix suggestions
"""
