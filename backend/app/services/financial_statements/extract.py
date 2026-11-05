"""Page-map driven extraction from statement faces.

Two layouts are supported:
- Embedded-text faces (HUBC, NML): labels on their own lines, values
  on following lines (or the same line), note references skipped.
- OGDC two-panel pages: one page holds the equity/liabilities
  panel (left) and the assets panel (right) side by side. The
  primary read is embedded text (interleaved document order);
  the page-match re-read uses the joint two-panel parser on
  pdftotext layout lines. The OCR renderers are retained code
  for image-only pages; no current sample map uses them.

A row spec is {"label": <printed label or null for a bare subtotal>,
"key": <canonical key>, "original_label": <label as printed>}.
Specs must be in printed order. Matching is sequential (a cursor),
so repeated labels resolve to their next occurrence.
"""

from __future__ import annotations

import re

from .numbers import is_note_ref, normalise_text, parse_number

_NUM_TOKEN_RE = re.compile(r"^\(?[\d,]+(\.\d+)?\)?$")
_SKIP_LINE_RES = [
    re.compile(r"ordinary shares", re.IGNORECASE),
    re.compile(r"shares of rupees", re.IGNORECASE),
]


def _clean_token(token: str) -> str:
    """Strip OCR/punctuation artifacts from a whitespace token."""
    t = token.strip().strip("_").strip("}").strip("«").strip()
    return t


def _token_value(token: str):
    """Return (numeric_or_None, is_value_token, sign_inferred).

    OCR artifacts stuck to a number ("—«-110,865,473",
    "«155,819,441", "1,307,054,273_") still yield their numeric
    core, provided the token contains no letters (so identifiers
    like "CS-04-08" never parse as values). A trailing ")" without
    "(" marks sign_inferred, per numbers.parse_number.
    """
    t = _clean_token(token)
    if t.lower() in ("-", "--", "nil"):
        return None, True, False
    if re.search(r"[A-Za-z]", t):
        return None, False, False
    m = re.search(r"\(?[\d,]+(\.\d+)?\)?", t)
    if m:
        value, _missing, sign_inferred = parse_number(m.group(0))
        if value is None:
            # Fragment, not a value: "(30" from "(30 June 2024: ...)"
            # must never occupy a column with NULL.
            return None, False, False
        return value, True, sign_inferred
    return None, False, False


def _strip_leading_junk(toks):
    """Drop tokens between a label and its values.

    Skips stray words and a punctuation dash ("Income tax-
    advance": the "-" before "advance" is label punctuation, not a
    missing value). A dash followed by a number (or at end) IS a
    missing value and is kept. A leading note reference is consumed.
    """
    rest = list(toks)
    skips = 0
    while rest and skips < 20:
        tok = rest[0]
        if is_note_ref(_clean_token(tok)):
            return rest[1:]
        _v, is_val, _s = _token_value(tok)
        if _v is not None:
            return rest
        if is_val:  # standalone dash
            if len(rest) > 1:
                _nv, nxt_is_val, _ns = _token_value(rest[1])
                if not nxt_is_val and not is_note_ref(_clean_token(rest[1])):
                    rest = rest[1:]
                    skips += 1
                    continue
            return rest
        rest = rest[1:]
        skips += 1
    return rest


def _line_value_tokens(line: str):
    """Numeric tokens on one line, in order, with missing flags."""
    out = []
    for raw in line.split():
        value, is_value, sign_inferred = _token_value(raw)
        if is_value:
            out.append((value, sign_inferred, raw))
    return out


def _is_skip_line(line: str) -> bool:
    return any(rx.search(line) for rx in _SKIP_LINE_RES)


def _is_skip_line_with_lookahead(lines, j: int) -> bool:
    """Whether line j contributes no values.

    True when the line itself carries the skip marker AND nothing
    follows the unit phrase, or when the NEXT line carries the
    marker (NML prints the share count and its "ordinary shares"
    unit on separate lines: the count line must be skipped too,
    or the share count is taken as the capital value).
    """
    if _is_skip_line(lines[j][1]):
        return _strip_share_context(lines[j][1]) == ""
    if j + 1 < len(lines) and _is_skip_line(lines[j + 1][1]):
        return True
    return False


def _strip_share_context(text: str) -> str:
    """Drop a share-count unit phrase and everything before it.

    NML prints values ON the "ordinary shares" line in one
    extractor's layout ("ordinary shares of Rupees 10 each
    3,515,999 3,515,999") and on later lines in another's. Keep
    only the tokens after "each" so the values survive in both
    layouts; return "" when nothing follows.
    """
    toks = text.split()
    lower = [t.lower().strip(".,") for t in toks]
    if "ordinary" not in lower:
        return text
    start = lower.index("ordinary")
    if "each" in lower[start:]:
        cut = start + lower[start:].index("each")
        return " ".join(toks[cut + 1 :])
    return ""


def _find_label(lines, start, label):
    """Find a label at/after start. Returns (index, joined) where
    joined True means the label spans two consecutive lines.

    A join match is accepted only when the label is genuinely
    split across the boundary (first word on line i, last word on
    line i+1, full label on neither alone). Otherwise a label
    sitting wholly on line i+1 would false-match at line i and
    steal the next row's values.
    """
    want = normalise_text(label)
    words = want.split()
    for i in range(start, len(lines)):
        text = normalise_text(lines[i][1])
        if want in text:
            return i, False
        if i + 1 < len(lines):
            nxt = normalise_text(lines[i + 1][1])
            if want in nxt:
                continue
            joined = normalise_text(lines[i][1] + " " + lines[i + 1][1])

            # Dash runs from the values' columns glue onto the
            # second line's last word ("interest---(954,006)"), so
            # split tokens on non-alphanumerics before comparing.
            def _parts(s):
                out = []
                for tok in s.split():
                    out.extend(p for p in re.split(r"[^a-z0-9]+", tok) if p)
                return out

            first_words = _parts(text)
            last_words = _parts(nxt)
            if want in joined and words and words[0] in first_words and words[-1] in last_words:
                return i, True
    return None, False


def extract_face(lines, specs, n_cols):
    """Extract one statement face.

    ``lines`` is a list of (page_no, text). Returns a list of row
    dicts with original_label, canonical key, displayed + numeric
    values per column, page number, and flags.
    """
    rows, _cursor = extract_face_from(lines, specs, n_cols, 0)
    return rows


def extract_face_from(lines, specs, n_cols, start, scan_cap=12):
    """Extract specs starting at line index ``start``.

    Used by matrix faces (changes-in-equity statements), where
    several movement blocks share one page and each block's specs
    must resolve to their next occurrence after the previous block.
    Returns (rows, end_cursor): the line index just past the last
    consumed line, so the next block can continue from it.
    ``scan_cap`` bounds how many lines a labeled row may scan for
    its values (default 12, as in run 1); matrix faces pass a larger
    cap because one row's values may occupy 16 separate lines in
    content-stream order. The next-spec label break remains the
    primary over-consumption guard at any cap.
    """
    rows = []
    cursor = start
    for si, spec in enumerate(specs):
        label = spec.get("label")
        row = {
            "key": spec["key"],
            "original_label": spec.get(
                "original_label", label or "(section subtotal, label not printed)"
            ),
            "displayed": [],
            "values": [],
            "page": None,
            "flags": [],
            "sign_inferred": False,
        }
        if label is None:
            # Bare subtotal: next n_cols numeric tokens after cursor.
            # A lone note reference on its own line is skipped, not
            # taken as a value (HUBC EPS total: note 43 precedes
            # 38.26 / 35.56); share-count lines are skipped via the
            # same lookahead as the labeled path.
            # skip_values: leading value tokens to skip before
            # collecting (dual-currency faces print USD columns
            # before PKR columns in content-stream order, so an
            # HBL bare row needs skip_values=2 to collect PKR).
            collected = []
            j = cursor
            skip = spec.get("skip_values", 0)
            skipped = 0
            while j < len(lines) and len(collected) < n_cols:
                if _is_skip_line_with_lookahead(lines, j):
                    j += 1
                    continue
                collectable = _strip_share_context(lines[j][1])
                toks = collectable.split()
                if len(toks) == 1 and is_note_ref(_clean_token(toks[0])):
                    j += 1
                    continue
                for value, sign_inferred, raw in _line_value_tokens(collectable):
                    if skipped < skip:
                        skipped += 1
                        continue
                    collected.append((value, sign_inferred, raw, lines[j][0]))
                    if len(collected) >= n_cols:
                        break
                j += 1
            cursor = j
            row["flags"].append("subtotal_position_inferred")
            if len(collected) < n_cols:
                row["flags"].append("incomplete_values")
            _fill_row(row, collected, n_cols)
            rows.append(row)
            continue
        # label_parts: a label split across NON-consecutive lines
        # with value lines interleaved (HBL CF: the first half of
        # the translation row's label prints, then the USD value
        # pair, then the second half, then the PKR pair — so the
        # two-consecutive-line join in _find_label cannot match).
        # Each part must match a single line, in order; values are
        # collected after the LAST part's line. The full label
        # stays in spec["label"] for the record; label_parts only
        # states how it is matched.
        effective_label = label
        label_parts = spec.get("label_parts")
        if label_parts:
            idx = None
            joined = False
            search_from = cursor
            for part in label_parts:
                found, part_joined = _find_label(lines, search_from, part)
                if found is None:
                    idx = None
                    break
                idx = found
                joined = part_joined
                search_from = found + 1
            effective_label = label_parts[-1]
        else:
            idx, joined = _find_label(lines, cursor, label)
        if idx is None:
            row["flags"].append("label_not_found")
            _fill_row(row, [], n_cols)
            rows.append(row)
            continue
        label_line_no = lines[idx][0]
        row["page"] = label_line_no
        # Values on the label line itself (after the label text),
        # skipping a leading note reference.
        collected = []
        label_text = normalise_text(lines[idx][1])
        want = normalise_text(effective_label)
        pos = label_text.lower().find(want.lower())
        remainder = lines[idx][1]
        # The last word must come from the RAW label, not the
        # normalised one: normalise merges hyphen spacing, so a
        # label ending "2023- (Audited)" normalises to a single
        # word "2023-(audited)" that no raw token matches, and the
        # remainder then falls back to the full line (leaking the
        # year "2023" in as a value).
        last_word = normalise_text(effective_label.split()[-1]).rstrip(".,-")
        if pos >= 0:
            # Recompute remainder from the raw line: take tokens
            # after the label's last word.
            toks = lines[idx][1].split()
            cut = None
            for k, tok in enumerate(toks):
                if normalise_text(tok).lower().rstrip(".,-") == last_word:
                    cut = k
            if cut is not None:
                remainder = " ".join(toks[cut + 1 :])
        if joined:
            # Values follow the label's last word on the second
            # line of the wrapped label (e.g. NML EPS values sit on
            # the "- BASIC AND DILUTED (RUPEES)" line itself).
            toks2 = lines[idx + 1][1].split()
            cut2 = None
            for k, tok in enumerate(toks2):
                if normalise_text(tok).rstrip(".,-") == last_word:
                    cut2 = k
            remainder = " ".join(toks2[cut2 + 1 :]) if cut2 is not None else ""
        if remainder.strip():
            toks = _strip_leading_junk(_strip_share_context(remainder).split())
            for raw in toks:
                value, is_value, sign_inferred = _token_value(raw)
                if is_value:
                    collected.append((value, sign_inferred, raw, label_line_no))
        j = idx + (2 if joined else 1)
        next_label = None
        # Peek at the next spec's label to avoid over-consumption.
        # (Bare next specs have no label; fall back to a line cap.)
        if si + 1 < len(specs) and specs[si + 1].get("label"):
            next_label = normalise_text(specs[si + 1]["label"])
        scanned = 0
        while j < len(lines) and len(collected) < n_cols and scanned < scan_cap:
            text = lines[j][1]
            if next_label and next_label in normalise_text(text):
                break
            if not _is_skip_line_with_lookahead(lines, j):
                toks = _strip_share_context(text).split()
                # Skip a leading note reference on its own line.
                if len(toks) == 1 and is_note_ref(_clean_token(toks[0])):
                    j += 1
                    scanned += 1
                    continue
                for raw in toks:
                    value, is_value, sign_inferred = _token_value(raw)
                    if is_value:
                        collected.append((value, sign_inferred, raw, lines[j][0]))
                        if len(collected) >= n_cols:
                            break
            j += 1
            scanned += 1
        cursor = j
        # blank_columns: column indices whose cell is BLANK in the
        # source (no dash, no value — verified by word positions,
        # HBL CE 2024 equity row: the NCI cell is empty while the
        # total column carries the value). Applies ONLY when the
        # collected token count fits exactly (tokens ==
        # n_cols - len(blanks)); otherwise the row stays
        # incomplete and gates out as usual. A blank cell records
        # None, exactly as a printed dash does — no value is
        # invented, and the block's rollforward/balance gates
        # still verify the declared position.
        blanks = spec.get("blank_columns") or []
        if blanks and len(collected) == n_cols - len(blanks):
            blank_set = set(blanks)
            rebuilt = []
            ti = 0
            for ci in range(n_cols):
                if ci in blank_set:
                    rebuilt.append((None, False, None, label_line_no))
                else:
                    rebuilt.append(collected[ti])
                    ti += 1
            collected = rebuilt
            row["flags"].append("blank_column_recorded")
        if len(collected) < n_cols:
            row["flags"].append("incomplete_values")
        _fill_row(row, collected, n_cols)
        rows.append(row)
    return rows, cursor


def _fill_row(row, collected, n_cols):
    for value, sign_inferred, raw, _page in collected[:n_cols]:
        row["displayed"].append(raw)
        row["values"].append(value)
        if sign_inferred:
            row["sign_inferred"] = True
    while len(row["values"]) < n_cols:
        row["values"].append(None)
        row["displayed"].append(None)
    if row["sign_inferred"]:
        row["flags"].append("sign_inferred_from_closing_paren")


def split_two_panel_line(line, right_labels):
    """Split an OGDC OCR line into (left_text, right_text).

    The right panel starts at the earliest occurrence of any known
    right-panel label. If none occurs, the whole line is left text.
    """
    norm = normalise_text(line)
    best = None
    for label in right_labels:
        want = normalise_text(label)
        pos = norm.lower().find(want.lower())
        if pos >= 0 and (best is None or pos < best[0]):
            best = (pos, want)
    if best is None:
        return line, ""
    # Map back to the raw line by character position approximation:
    # re-find in the raw line case-insensitively.
    raw_lower = line.lower()
    pos = raw_lower.find(best[1].lower())
    if pos < 0:
        return line, ""
    return line[:pos], line[pos:]


def ocr_page_lines(pdf_path, page_no, dpi=200):
    """Render one PDF page and OCR it. Returns [(page_no, line)].

    Raises ValueError (not a traceback from the subprocess module)
    when the tesseract executable is missing, so callers can
    fail fast with a clean abort.
    """
    import shutil
    import subprocess
    import tempfile

    if shutil.which("tesseract") is None:
        raise ValueError("tesseract executable not found; OCR extraction cannot run")

    import pymupdf

    doc = pymupdf.open(pdf_path)
    page = doc[page_no - 1]
    pix = page.get_pixmap(dpi=dpi)
    doc.close()
    with tempfile.TemporaryDirectory() as tmp:
        img = f"{tmp}/page.png"
        pix.save(img)
        out = subprocess.run(
            ["tesseract", img, "stdout", "--psm", "6"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        return [(page_no, ln) for ln in out.stdout.splitlines()]


def _same_line_values(text, label, n_cols):
    """Numeric tokens after a label on the same OCR line.

    Skips a leading note reference. Returns (collected, found_label).
    """
    want = normalise_text(label)
    norm = normalise_text(text)
    pos = norm.lower().find(want.lower())
    if pos < 0:
        return [], False
    # Tokens after the label's last word, from the RAW line. The
    # last word comes from the raw label: normalise merges hyphen
    # spacing, so a label ending "2023- (Audited)" would otherwise
    # never match a raw token (same trap as extract_face_from).
    last_word = normalise_text(label.split()[-1]).lower().rstrip(".,-")
    toks = text.split()
    cut = None
    for k, tok in enumerate(toks):
        if normalise_text(tok).lower().rstrip(".,-") == last_word:
            cut = k
    if cut is None:
        return [], True
    rest = _strip_leading_junk(toks[cut + 1 :])
    collected = []
    for raw in rest:
        value, is_value, sign_inferred = _token_value(raw)
        if is_value:
            collected.append((value, sign_inferred, raw))
            if len(collected) >= n_cols:
                break
    return collected, True


def extract_ogdc_face(lines, left_specs, right_specs, right_labels, n_cols=2):
    """Joint parse of one OGDC two-panel page (layout lines).

    A single pass maintains a spec cursor per panel. A numbers-only
    line with four tokens feeds the next bare spec of BOTH panels
    (the grand-total line); with two tokens it feeds the next bare
    spec of the panel of the most recently matched row. Returns
    (left_rows, right_rows).
    """
    left_rows: dict[str, dict] = {}
    right_rows: dict[str, dict] = {}
    li = ri = 0
    last_panel = None

    def _row_for(spec, page):
        return {
            "key": spec["key"],
            "original_label": spec.get(
                "original_label", spec.get("label") or "(section subtotal, label not printed)"
            ),
            "displayed": [],
            "values": [],
            "page": page,
            "flags": [],
            "sign_inferred": False,
        }

    def _consume_bare(store, specs, idx, tokens, page):
        row = _row_for(specs[idx], page)
        row["flags"].append("subtotal_position_inferred")
        _fill_row(row, [(v, s, r, page) for v, s, r in tokens[:n_cols]], n_cols)
        store[specs[idx]["key"]] = row
        return idx + 1

    def _all_same_line_tokens(text, label):
        """All numeric tokens after a label on one OCR line."""
        want = normalise_text(label)
        norm = normalise_text(text)
        pos = norm.lower().find(want.lower())
        if pos < 0:
            return []
        last_word = want.split()[-1].lower().rstrip(".,-")
        toks = text.split()
        cut = None
        for k, tok in enumerate(toks):
            if normalise_text(tok).lower().rstrip(".,-") == last_word:
                cut = k
        if cut is None:
            return []
        rest = _strip_leading_junk(toks[cut + 1 :])
        out = []
        for raw in rest:
            value, is_value, sign_inferred = _token_value(raw)
            if is_value:
                out.append((value, sign_inferred, raw))
        return out

    def _side_tokens(text):
        out = []
        for raw in text.split():
            value, is_value, sign_inferred = _token_value(raw)
            if is_value:
                out.append((value, sign_inferred, raw))
        return out

    def _consumed_count(side_toks, collected):
        """Value tokens consumed by a matched row: the span up to
        its last collected raw token. Note references ("8") count
        as value tokens in side_toks but are skipped by the row
        matcher, so min(len, n_cols) would undercount."""
        j = 0
        for i, (_v, _s, raw) in enumerate(side_toks):
            if j < len(collected) and raw == collected[j][2]:
                j += 1
                if j == len(collected):
                    return i + 1
        return len(side_toks)

    for page_no, text in lines:
        left_text, right_text = split_two_panel_line(text, right_labels)
        left_all = _side_tokens(left_text)
        right_all = _side_tokens(right_text)
        left_consumed = 0
        right_consumed = 0
        # Left panel labeled row? A label with no value on its line
        # (e.g. a section header "SHARE CAPITAL AND RESERVES") is NOT
        # a match: it must not consume the spec.
        if li < len(left_specs) and left_specs[li].get("label"):
            collected, found = _same_line_values(left_text, left_specs[li]["label"], n_cols)
            if found and collected:
                row = _row_for(left_specs[li], page_no)
                if len(collected) < n_cols:
                    row["flags"].append("incomplete_values")
                _fill_row(row, [(v, s, r, page_no) for v, s, r in collected], n_cols)
                left_rows[left_specs[li]["key"]] = row
                li += 1
                last_panel = "left"
                left_consumed = _consumed_count(left_all, collected)
        # Right panel labeled row? Same header guard.
        if ri < len(right_specs) and right_specs[ri].get("label"):
            collected, found = _same_line_values(right_text, right_specs[ri]["label"], n_cols)
            if found and collected:
                row = _row_for(right_specs[ri], page_no)
                if len(collected) < n_cols:
                    row["flags"].append("incomplete_values")
                _fill_row(row, [(v, s, r, page_no) for v, s, r in collected], n_cols)
                right_rows[right_specs[ri]["key"]] = row
                ri += 1
                last_panel = "right"
                right_consumed = _consumed_count(right_all, collected)
        # Bare specs. Tokens left on a side after its labeled match
        # belong to the OTHER panel (e.g. the TOTAL LIABILITIES line
        # also carries the right current-assets total); tokens on a
        # side whose panel did not match and whose next spec is
        # labeled are free for the other panel's bare spec (e.g. a
        # right bare total on a line whose split found no right
        # label); tokens on a side whose next spec is bare are its
        # own subtotal.
        left_left = left_all[left_consumed:]
        right_left = right_all[right_consumed:]
        left_is_bare = li < len(left_specs) and not left_specs[li].get("label")
        right_is_bare = ri < len(right_specs) and not right_specs[ri].get("label")
        if left_is_bare and left_consumed == 0 and len(left_left) == n_cols:
            li = _consume_bare(left_rows, left_specs, li, left_left, page_no)
            left_left = []
        if right_is_bare and right_consumed == 0 and len(right_left) == n_cols:
            ri = _consume_bare(right_rows, right_specs, ri, right_left, page_no)
            right_left = []
        left_is_bare = li < len(left_specs) and not left_specs[li].get("label")
        right_is_bare = ri < len(right_specs) and not right_specs[ri].get("label")
        pool = left_left + right_left
        if left_is_bare and right_is_bare and len(pool) == 2 * n_cols:
            li = _consume_bare(left_rows, left_specs, li, pool[:n_cols], page_no)
            ri = _consume_bare(right_rows, right_specs, ri, pool[n_cols:], page_no)
            last_panel = None
        elif left_is_bare and not right_is_bare and len(pool) == n_cols:
            li = _consume_bare(left_rows, left_specs, li, pool, page_no)
        elif right_is_bare and not left_is_bare and len(pool) == n_cols:
            ri = _consume_bare(right_rows, right_specs, ri, pool, page_no)
        elif left_is_bare and right_is_bare and len(pool) == n_cols:
            # Both bare, one pair of tokens: it belongs to the panel
            # opposite the side that matched a labeled row.
            if left_consumed > 0 and right_consumed == 0:
                ri = _consume_bare(right_rows, right_specs, ri, pool, page_no)
            elif right_consumed > 0 and left_consumed == 0:
                li = _consume_bare(left_rows, left_specs, li, pool, page_no)
            elif last_panel == "right":
                ri = _consume_bare(right_rows, right_specs, ri, pool, page_no)
            else:
                li = _consume_bare(left_rows, left_specs, li, pool, page_no)
    # Flag unmatched specs.
    for idx in range(li, len(left_specs)):
        row = _row_for(left_specs[idx], None)
        row["flags"].append("label_not_found")
        _fill_row(row, [], n_cols)
        left_rows[left_specs[idx]["key"]] = row
    for idx in range(ri, len(right_specs)):
        row = _row_for(right_specs[idx], None)
        row["flags"].append("label_not_found")
        _fill_row(row, [], n_cols)
        right_rows[right_specs[idx]["key"]] = row
    left_ordered = [left_rows[s["key"]] for s in left_specs]
    right_ordered = [right_rows[s["key"]] for s in right_specs]
    return left_ordered, right_ordered
