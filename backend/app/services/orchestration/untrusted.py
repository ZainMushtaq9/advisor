"""Phase 18 untrusted-data controls.

Retrieved web pages, files, news items, and documents are data,
never instructions. Every untrusted input is classified before
it reaches an agent: instructional language is flagged, never
followed, and a flagged input quarantines its task. The original
text is preserved in the audit evidence (truncated) so the
quarantine is reviewable; it is never executed, never pasted
into a prompt without a boundary, and never allowed to re-task
an agent.

Classification is pattern-based and deliberately narrow: it
flags imperative override language, not ordinary prose. A
benign sentence about a company ("HUBC reported a profit")
carries no flag. False negatives remain possible, which is why
the deterministic-authority check (validation.py) is the second
layer: even a missed injection cannot change a stored value.
"""

from __future__ import annotations

import re

# Imperative override patterns. Each is an instruction aimed at
# the agent or the system, not a statement about a company.
_INSTRUCTION_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"ignore (all |any )?(previous|prior|above) instructions", re.IGNORECASE),
    re.compile(r"disregard (all )?(previous|prior|above|system) instructions", re.IGNORECASE),
    re.compile(
        r"override (the )?(stored|recorded|system|previous) (value|price|close|instruction)",
        re.IGNORECASE,
    ),
    re.compile(r"\bset the \w+ (close|price|value) to\b", re.IGNORECASE),
    re.compile(r"you are now (a|an|the)\b", re.IGNORECASE),
    re.compile(r"new (system )?instruction(s)?:", re.IGNORECASE),
    re.compile(r"send (this|it|the data) (elsewhere|to|outside)", re.IGNORECASE),
    re.compile(r"do not (follow|obey|apply) (the )?(system|previous|above)", re.IGNORECASE),
    re.compile(r"forget (the )?(system|previous|above) (prompt|instructions|rules)", re.IGNORECASE),
)


def classify_untrusted(content: str) -> dict:
    """Classify an untrusted input blob.

    Returns {"trust": "UNTRUSTED", "flags": [...], "quarantine":
    bool}. ``flags`` names each matched pattern class. An empty
    flag list means no instructional language was detected — not
    a guarantee of safety, which is why downstream validation
    still applies.
    """
    flags: list[str] = []
    for pattern in _INSTRUCTION_PATTERNS:
        if pattern.search(content):
            flags.append(pattern.pattern)
    return {
        "trust": "UNTRUSTED",
        "flags": flags,
        "quarantine": bool(flags),
    }


def wrap_untrusted(content: str, source: str) -> dict:
    """Wrap an untrusted blob with provenance and classification.

    The wrapped form is what an agent receives: content plus an
    explicit UNTRUSTED marker, its source, and its flags. The
    wrapper is the boundary: nothing inside ``content`` is ever
    treated as an instruction to the agent.
    """
    classification = classify_untrusted(content)
    return {
        "source": source,
        "trust": "UNTRUSTED",
        "content_preview": content[:280],
        "flags": classification["flags"],
        "quarantine": classification["quarantine"],
    }
