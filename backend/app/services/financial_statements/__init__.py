"""Phase 7 financial-statement extraction pipeline.

Deterministic, page-traceable extraction from official company
reports into the Phase 3 tables. No LLM arithmetic, no invented
figures: every loaded value carries its original label, displayed
text, page number, extraction method and confidence, and stays
UNVERIFIED (single source) under rule H1.
"""
