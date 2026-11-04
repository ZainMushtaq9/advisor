# Phase 18 Untrusted-Data Controls

Implemented in `backend/app/services/orchestration/untrusted.py` and
`backend/app/services/orchestration/validation.py`.

## Principle

Retrieved web pages, files, news items, announcements, and documents are
**data, never instructions**. Tool output is never pasted into a prompt
without a boundary, and retrieved text never overrides system instructions
or re-tasks an agent.

## Layers

1. **Classification before use.** Every untrusted input blob is classified
   for imperative override language (e.g. "ignore previous instructions",
   "set the X close to …", "you are now …", "send this elsewhere"). A
   flagged blob quarantines its task: the output is not stored as a fact
   and the task is marked QUARANTINED with the flags in its checkpoint.
2. **Provenance wrapper.** An agent receives untrusted content only inside
   a wrapper carrying an explicit UNTRUSTED marker, its source, a truncated
   preview, and its flags. The wrapper is the boundary.
3. **Deterministic authority (second layer).** Even a missed injection
   cannot change a stored value: a numeric claim is compared against the
   deterministic service value. Equal + evidence → ACCEPT. Different →
   QUARANTINE_MISMATCH. No evidence reference → QUARANTINE_NO_EVIDENCE
   (a correct guess without evidence is still not evidence). No service
   value → QUARANTINE_NO_SERVICE_VALUE (unverifiable, not accepted).
   No verdict ever modifies the stored row.
4. **Audit preservation.** The original flagged text is preserved
   (truncated) in audit evidence so the quarantine is reviewable. It is
   never executed and never followed.

## Known limitation

Pattern classification can miss novel injection phrasing (false negatives
remain possible). That is why deterministic authority is a separate layer
rather than a fallback: the two layers fail independently. Classification
quality is measured by the stored evaluation rows, not asserted.
