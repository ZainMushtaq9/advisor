"""Phase 19 hybrid retrieval: full-text + metadata + exact identifier.

Deterministic, dependency-free scoring over stored chunks:

- Tokenisation lowercases, splits on non-alphanumerics, and
  drops a small stopword list. Numbers keep their digits and
  their comma/decimal forms are normalised ("56,257,178" and
  "56257178" tokenise to the same token), so a figure query
  matches the passage that prints it.
- Score = 2.0 per distinct query token present + 5.0 exact-phrase
  bonus (the full normalised query string appearing in the chunk)
  + 3.0 exact-identifier bonus (a queried ticker token matching
  the chunk's company; company names resolve to tickers, so
  "Nishat Mills" earns the NML bonus exactly as "NML" does)
  + 2.0 structured-section bonus (statement faces and the
  auditor opinion outrank narrative body pages). A chunk
  scoring 0 is never returned.
- Metadata filters apply BEFORE scoring: company (ticker),
  document type, as-of date (publication_date <= as_of; a
  document with publication_date NULL is excluded by any as-of
  filter that requires a known date — its date is unknown, never
  assumed), and caller access level (see access.py).
- Dedup: at most one chunk per (document, page) — the highest
  scoring — so a long face page does not flood the top-k.
- Injection-flagged chunks are never returned, whatever their
  score.
- Snippets are capped at SNIPPET_MAX_CHARS (500) and centred
  on the first matched query token: a citation must show the
  passage that matched, not the page start. Retrieval serves
  a passage plus a page-level citation, never a full page or
  document, so no unlicensed document is redistributed.
- Vector retrieval is NOT implemented (see services/rag
  __init__); search() never claims a vector score.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.services.rag import SNIPPET_MAX_CHARS

STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "of",
        "to",
        "in",
        "on",
        "for",
        "was",
        "were",
        "is",
        "are",
        "what",
        "which",
        "who",
        "did",
        "does",
        "how",
        "when",
        "by",
        "at",
        "as",
        "with",
        "from",
        "its",
        "it",
        "that",
        "this",
        "these",
        "those",
        "be",
        "been",
        "has",
        "have",
        "had",
        "per",
        "year",
        "ended",
    }
)

TICKER_RE = re.compile(r"^[A-Z]{2,10}\d?[A-Z0-9]*$")

# Company-name resolution for the identifier bonus: a query
# naming "Nishat Mills" must resolve to NML exactly as a query
# naming "NML" does. Keys are normalised token tuples; the map
# covers the indexed companies plus HBL (pending) so a missing
# company's name still resolves for the missing-data path.
COMPANY_NAME_TOKENS: dict[tuple[str, ...], str] = {
    ("nishat", "mills"): "NML",
    ("hub", "power"): "HUBC",
    ("hubco",): "HUBC",
    ("oil", "gas", "development"): "OGDC",
    ("ogdc",): "OGDC",
    ("habib", "bank"): "HBL",
}

# Structured sections (statement faces, auditor opinion) carry
# a small ranking bonus over narrative body pages: a face page
# is the authoritative location for the figure it reports.
SECTION_BONUS = 2.0


def normalise_number_token(token: str) -> str:
    """Strip thousands separators so 56,257,178 == 56257178."""
    return token.replace(",", "")


def tokenise(text: str) -> list[str]:
    raw = re.findall(r"[A-Za-z0-9][A-Za-z0-9,\.]*", text.lower())
    tokens: list[str] = []
    for token in raw:
        token = token.strip(".,")
        if not token or token in STOPWORDS:
            continue
        tokens.append(normalise_number_token(token))
    return tokens


def token_set(text: str) -> set[str]:
    return set(tokenise(text))


@dataclass
class ScoredChunk:
    chunk_id: int
    document_id: int
    ticker: str
    title: str
    page_number: int
    section_label: str
    text: str
    score: float
    matched_tokens: list[str] = field(default_factory=list)
    factoid: bool = False

    def snippet(self, max_chars: int = SNIPPET_MAX_CHARS) -> str:
        """Extractive snippet: the max_chars window of the chunk
        that best evidences the query. For factoid questions
        ("what was …", "how much …") the window centres on the
        figure whose neighbouring row label best matches the
        question; otherwise matched-token density wins with
        figures as a tiebreak. A citation must show the
        passage that matched, not the page start: a
        first-500-chars snippet can cite a page without showing
        the evidence on it."""
        if len(self.text) <= max_chars:
            return self.text
        window = _best_evidence_window(
            self.text,
            self.matched_tokens,
            max_chars,
            factoid=self.factoid,
        )
        if window is None:
            return self.text[:max_chars].rstrip() + " …"
        start, end = window
        snippet = self.text[start:end].strip()
        prefix = "… " if start > 0 else ""
        suffix = " …" if end < len(self.text) else ""
        return prefix + snippet + suffix

    def citation(self) -> dict:
        return {
            "ticker": self.ticker,
            "title": self.title,
            "page": self.page_number,
            "section": self.section_label,
            "chunk_id": self.chunk_id,
            "snippet": self.snippet(),
        }


def _token_spans(text: str) -> list[tuple[str, int, int]]:
    """(normalised token, start, end) spans, using the same
    tokeniser as scoring, so comma-grouped figures
    ("56,257,178" vs token "56257178") still locate."""
    spans: list[tuple[str, int, int]] = []
    for match in re.finditer(r"[A-Za-z0-9][A-Za-z0-9,\.]*", text):
        token = normalise_number_token(match.group(0).lower().strip(".,"))
        if token:
            spans.append((token, match.start(), match.end()))
    return spans


FACTOID_MARKERS = ("what was", "what were", "how much", "how many")


def is_factoid_query(query: str) -> bool:
    lowered = query.lower()
    return any(marker in lowered for marker in FACTOID_MARKERS)


def _is_figure_token(token: str) -> bool:
    """A figure: a number token of 5+ digits (thousands-scale
    values in these statements; years and page numbers are
    4 digits or fewer and never qualify)."""
    return token.isdigit() and len(token) >= 5


def _best_evidence_window(
    text: str,
    matched_tokens: list[str],
    max_chars: int,
    factoid: bool = False,
) -> tuple[int, int] | None:
    """Best (start, end) window of at most max_chars.

    Factoid questions ("what was …"): windows centre on
    figure tokens, scored by distinct matched tokens within
    ±150 chars of the figure — the row label next to the
    figure is what identifies it ("NET PROFIT FOR THE YEAR"
    next to 56,257,178 beats "Revenue … net" next to a
    revenue figure, because the profit row carries both
    "net" and "profit"). A dense header full of period
    tokens but no figure never wins a factoid snippet.
    Other questions: token-anchored windows scored by
    (distinct matched tokens, figure tiebreak). Ties go to
    the earliest window. None when no matched token occurs
    in the text (or, for factoid, no figure occurs)."""
    if not matched_tokens:
        return None
    wanted = set(matched_tokens)
    spans = _token_spans(text)
    matched_spans = [s for s in spans if s[0] in wanted]
    if not matched_spans:
        return None
    if factoid:
        figure_spans = [s for s in spans if _is_figure_token(s[0])]
        if figure_spans:
            best_fig: tuple[int, int, int] | None = None
            for _, figure_start, _ in figure_spans:
                local = {
                    token for token, span_start, _ in spans if abs(span_start - figure_start) <= 150
                }
                distinct = len(local & wanted)
                if best_fig is None or distinct > best_fig[0]:
                    start = max(0, figure_start - 250)
                    end = min(len(text), start + max_chars)
                    best_fig = (distinct, start, end)
            if best_fig is not None:
                return best_fig[1], best_fig[2]
    best_key: tuple[int, int] | None = None
    best_window: tuple[int, int] | None = None
    for _, anchor_start, _ in matched_spans:
        start = anchor_start
        end = min(len(text), start + max_chars)
        window_tokens = {token for token, span_start, _ in spans if start <= span_start < end}
        distinct = len(window_tokens & wanted)
        figure = 1 if any(_is_figure_token(t) for t in window_tokens) else 0
        key = (distinct, figure)
        if best_key is None or key > best_key:
            best_key = key
            best_window = (start, end)
    return best_window


def score_chunk(
    query_tokens: set[str],
    query_phrase: str,
    query_tickers: set[str],
    chunk_text: str,
    chunk_ticker: str,
    section_label: str = "body",
) -> tuple[float, list[str]]:
    """Return (score, matched_tokens). Zero means no match."""
    if not query_tokens:
        return 0.0, []
    chunk_tokens = token_set(chunk_text)
    matched = sorted(query_tokens & chunk_tokens)
    if not matched:
        return 0.0, []
    score = 2.0 * len(matched)
    normalised_text = " ".join(tokenise(chunk_text))
    if query_phrase and query_phrase in normalised_text:
        score += 5.0
    if query_tickers and chunk_ticker in query_tickers:
        score += 3.0
    if section_label != "body":
        score += SECTION_BONUS
    return score, matched


def extract_query_tickers(query: str, known_tickers: set[str]) -> set[str]:
    found: set[str] = set()
    for word in re.findall(r"[A-Za-z]{2,10}\d?", query.upper()):
        if word in known_tickers:
            found.add(word)
    # Company-name resolution: "Nishat Mills" resolves to NML
    # exactly as "NML" does.
    query_token_list = tokenise(query)
    for length in (3, 2, 1):
        for start in range(len(query_token_list) - length + 1):
            key = tuple(query_token_list[start : start + length])
            ticker = COMPANY_NAME_TOKENS.get(key)
            if ticker is not None:
                found.add(ticker)
    return found


def search_chunks(
    query: str,
    chunks: list[dict],
    top_k: int = 5,
    ticker_filter: str | None = None,
    document_type_filter: str | None = None,
    as_of: object | None = None,
) -> list[ScoredChunk]:
    """Search pre-loaded chunk dicts. Each chunk dict carries:
    id, document_id, ticker, title, document_type,
    publication_date (a date or None), page_number,
    section_label, text, injection_flag. Injection-flagged
    chunks are excluded before scoring. Returns at most top_k
    ScoredChunks, deduped to one per (document, page), best
    score first (ties: lower page, then lower chunk id)."""
    query_tokens = set(tokenise(query))
    query_phrase = " ".join(tokenise(query))
    factoid = is_factoid_query(query)
    known_tickers = {c["ticker"] for c in chunks}
    query_tickers = extract_query_tickers(query, known_tickers)
    scored: list[ScoredChunk] = []
    for chunk in chunks:
        if chunk.get("injection_flag"):
            continue
        if ticker_filter and chunk["ticker"] != ticker_filter:
            continue
        if document_type_filter and chunk.get("document_type") != document_type_filter:
            continue
        if as_of is not None:
            pub = chunk.get("publication_date")
            if pub is None or pub > as_of:
                continue
        score, matched = score_chunk(
            query_tokens,
            query_phrase,
            query_tickers,
            chunk["text"],
            chunk["ticker"],
            section_label=chunk.get("section_label", "body"),
        )
        if score <= 0:
            continue
        scored.append(
            ScoredChunk(
                chunk_id=chunk["id"],
                document_id=chunk["document_id"],
                ticker=chunk["ticker"],
                title=chunk["title"],
                page_number=chunk["page_number"],
                section_label=chunk["section_label"],
                text=chunk["text"],
                score=score,
                matched_tokens=matched,
                factoid=factoid,
            )
        )
    scored.sort(key=lambda s: (-s.score, s.page_number, s.chunk_id))
    deduped: list[ScoredChunk] = []
    seen_pages: set[tuple[int, int]] = set()
    for item in scored:
        key = (item.document_id, item.page_number)
        if key in seen_pages:
            continue
        seen_pages.add(key)
        deduped.append(item)
        if len(deduped) >= top_k:
            break
    return deduped
