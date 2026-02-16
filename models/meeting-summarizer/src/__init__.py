"""
Client Meeting Summarizer — GenAI Model #2

Processes advisor-client meeting transcripts to produce:
  1. Structured meeting summary (2-3 sentences)
  2. Key discussion points (bulleted)
  3. Action items with owners and due dates
  4. Compliance flags (suitability, disclosures, complaints)
  5. Draft follow-up email (requires human review before send)

Architecture:
  - Input: Raw transcript text (from speech-to-text or manual)
  - Processing: LLM summarization with structured output
  - Compliance: NER for PII detection + rule-based compliance checks
  - Output: JSON structured summary + draft email + compliance report
  - Control: Human-in-the-loop required before any client communication

Mirrors: AI @ Morgan Stanley Debrief
"""
