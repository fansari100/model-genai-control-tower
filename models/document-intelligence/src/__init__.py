"""
WM Document Intelligence — GenAI Model #1

Extracts structured financial data from unstructured documents (prospectuses,
fund fact sheets, investment policy statements) using RAG + LLM structured output.

Architecture:
  1. Document ingestion → chunking → embedding (text-embedding-3-large)
  2. Vector store (ChromaDB) for semantic retrieval
  3. LLM extraction with Pydantic structured output (GPT-4o)
  4. Validation layer (business rules + cross-field consistency)

WM Use Case: Replaces manual document review for vendor model onboarding,
fund due diligence, and regulatory filing analysis.
"""
