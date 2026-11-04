"""Phase 19 document indexing: page extraction, chunking, injection scan.

- Extraction uses the PDF's embedded text only (the Phase 7
  finding that all three reports carry full embedded text still
  holds). No OCR rows are created: a page with no extractable
  text yields zero chunks, recorded as a gap, never as invented
  text.
- Chunking splits by page first, then by paragraph, capping each
  chunk at CHUNK_MAX_CHARS. A chunk keeps its page number and a
  section label: the Phase 7 face label when the page is a known
  face page, else "body". Tables keep their reporting context
  through that label plus the page citation.
- Injection scan (Phase 18 precedent): document text is data,
  never instructions. Patterns cover instruction override,
  price/value override, and secrecy suppression. A flagged
  chunk is stored with its flag and note but is EXCLUDED from
  retrieval and never cited. The patterns deliberately avoid
  ordinary financial wording ("the board resolved", "act as
  trustee") so legitimate passages are not quarantined.
- Hashing: SHA-256 over the chunk text; the document hash is
  SHA-256 over the file bytes, computed at index time and
  compared against the stored financial_documents content hash
  when present (a mismatch is reported, never silently fixed).
"""

from __future__ import annotations

import hashlib
import re

from app.services.rag import CHUNK_MAX_CHARS, FACE_PAGES

# A face page kept whole is still bounded: no chunk may exceed
# this, so a pathological page cannot become an unbounded chunk.
FACE_PAGE_MAX_CHARS = 12000

# Instructional-language patterns. Matching is deliberately
# narrow: ordinary financial wording ("the board resolved",
# "management decided") must not trip it. Each pattern targets
# an instruction directed at the reader/agent or an override of
# a stored value.
INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bignore (all )?(previous|prior|earlier) instructions\b", re.I),
    re.compile(r"\bdisregard (all )?(previous|prior) instructions\b", re.I),
    re.compile(r"\byou (must|should|will) (now )?(ignore|disregard|override)\b", re.I),
    re.compile(r"\bset the (price|close|value) (to|at)\b", re.I),
    re.compile(r"\boverride the (stored|recorded|official) (price|close|value)\b", re.I),
    re.compile(r"\bdo not (reveal|disclose|mention) (this|that|the)\b", re.I),
    re.compile(r"\bnew (system|user) instruction\b", re.I),
    re.compile(r"\bforget (your|the) (instructions|rules)\b", re.I),
)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def scan_injection(text: str) -> tuple[bool, str | None]:
    """Return (flagged, note). A flagged chunk is data, never an
    instruction: it is stored flagged and excluded from retrieval."""
    for pattern in INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            return True, (
                "Instructional language detected and quarantined: "
                f"matched pattern {pattern.pattern!r} on "
                f"{match.group(0)!r}. Chunk excluded from retrieval."
            )
    return False, None


def chunk_page_text(page_text: str, max_chars: int = CHUNK_MAX_CHARS) -> list[str]:
    """Split one page's text into chunks of at most max_chars,
    breaking at paragraph boundaries where possible. Empty pages
    yield no chunks."""
    paragraphs = [p.strip() for p in page_text.split("\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            # A single over-long paragraph splits on hard
            # character boundaries; content is preserved, only
            # split points change.
            if current:
                chunks.append(current)
                current = ""
            for start in range(0, len(paragraph), max_chars):
                chunks.append(paragraph[start : start + max_chars])
            continue
        if current and len(current) + 1 + len(paragraph) > max_chars:
            chunks.append(current)
            current = paragraph
        else:
            current = f"{current}\n{paragraph}" if current else paragraph
    if current:
        chunks.append(current)
    return chunks


def section_label_for(ticker: str, page_number: int) -> str:
    return FACE_PAGES.get(ticker, {}).get(page_number, "body")


def extract_pages(pdf_path: str) -> list[tuple[int, str]]:
    """Extract (1-based page number, text) pairs via PyMuPDF.
    Pages with no extractable text return empty text and are
    skipped by the caller (a gap, never invented content)."""
    import fitz  # PyMuPDF; already a backend dependency (Phase 12)

    pages: list[tuple[int, str]] = []
    with fitz.open(pdf_path) as doc:
        for index, page in enumerate(doc, start=1):
            pages.append((index, page.get_text()))
    return pages


def index_document_pages(pdf_path: str, ticker: str) -> list[dict]:
    """Full indexing pass for one document. Returns chunk dicts
    with page_number, section_label, chunk_index, text,
    text_hash, injection_flag, injection_note. Raises on a
    missing file; never synthesises a page.

    Face pages (statement faces, auditor opinion) are kept
    WHOLE: splitting a table mid-row separates labels from
    figures and destroys the reporting context the brief
    requires preserved. Body pages split at CHUNK_MAX_CHARS.
    A whole face page is still bounded (FACE_PAGE_MAX_CHARS)
    so no pathological page becomes an unbounded chunk."""
    chunk_rows: list[dict] = []
    for page_number, page_text in extract_pages(pdf_path):
        if not page_text.strip():
            continue
        label = section_label_for(ticker, page_number)
        if label != "body":
            page_chunks = [page_text.strip()]
            if len(page_chunks[0]) > FACE_PAGE_MAX_CHARS:
                page_chunks = chunk_page_text(page_text, FACE_PAGE_MAX_CHARS)
        else:
            page_chunks = chunk_page_text(page_text)
        for chunk_index, chunk in enumerate(page_chunks):
            flagged, note = scan_injection(chunk)
            chunk_rows.append(
                {
                    "page_number": page_number,
                    "section_label": label,
                    "chunk_index": chunk_index,
                    "text": chunk,
                    "text_hash": sha256_text(chunk),
                    "injection_flag": flagged,
                    "injection_note": note,
                }
            )
    return chunk_rows
