"""
Portfolio Risk Narrator — GenAI Model #3

Generates natural-language risk commentary from structured portfolio analytics data.
Transforms quantitative risk metrics into human-readable narratives for:
  - Client quarterly reports
  - Advisor briefing notes
  - Risk committee presentations
  - Regulatory filings

Architecture:
  - Input: Structured portfolio data (JSON: holdings, returns, risk metrics)
  - Processing: Data-to-text generation with quantitative reasoning (GPT-4o)
  - Validation: Fact-checking generated numbers against source data
  - Output: Professional risk narrative with citations to source metrics
"""
