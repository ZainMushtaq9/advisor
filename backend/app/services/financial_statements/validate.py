"""Pure validation for extracted statement faces.

All arithmetic is Decimal, deterministic, and traceable. A failed
check never adjusts a value: the statement is flagged and the
failure is recorded in the run report.
"""

from __future__ import annotations

from decimal import Decimal


def _get(rows, key, col):
    for row in rows:
        if row["key"] == key and len(row["values"]) > col:
            return row["values"][col]
    return None


def check_balance_identity(rows, col, equity_keys, liability_keys):
    """total_assets == total_equity + sum(liability components).

    ``equity_keys`` is normally ["total_equity"] (which already
    includes non-controlling interests where the face presents it so).
    ``liability_keys`` lists the liability totals to add. Returns
    (passed, detail_dict) with exact Decimal difference.
    """
    assets = _get(rows, "total_assets", col)
    equity = _get(rows, "total_equity", col)
    if assets is None or equity is None:
        return False, {"reason": "missing total_assets or total_equity"}
    total = equity
    missing = []
    for key in liability_keys:
        value = _get(rows, key, col)
        if value is None:
            missing.append(key)
        else:
            total += value
    if missing:
        return False, {"reason": "missing liability components", "keys": missing}
    diff = assets - total
    return diff == 0, {
        "total_assets": str(assets),
        "computed": str(total),
        "difference": str(diff),
    }


def check_cross_component(rows, row_key, total_idx, comp_indices, missing="zero"):
    """A balance-row total equals the sum of its components across
    the columns of a matrix face (changes-in-equity statements).

    ``rows`` is one movement block's rows; each row's ``values`` are
    per-component (component order = the map's component list).
    ``row_key`` selects the balance row (opening/closing);
    ``total_idx`` is the total component's index; ``comp_indices``
    are the summed components' indices. ``missing="zero"`` treats a
    printed dash (NULL) as contributing nothing, listing the keys
    — valid only where the missing value is a printed dash, never
    for a genuinely missed extraction (callers must also require
    zero flagged rows before trusting missing-as-zero).
    """
    row = None
    for r in rows:
        if r["key"] == row_key:
            row = r
            break
    if row is None:
        return False, {"reason": f"missing row {row_key}"}
    if total_idx >= len(row["values"]):
        return False, {"reason": f"total index {total_idx} out of range"}
    total = row["values"][total_idx]
    if total is None:
        return False, {"reason": f"missing total at index {total_idx}"}
    acc = Decimal(0)
    missing_keys = []
    for idx in comp_indices:
        value = row["values"][idx] if idx < len(row["values"]) else None
        if value is None:
            missing_keys.append(idx)
        else:
            acc += value
    if missing_keys and missing != "zero":
        return False, {"reason": "missing components", "indices": missing_keys}
    diff = total - acc
    return diff == 0, {
        "total": str(total),
        "computed": str(acc),
        "difference": str(diff),
        "missing_as_zero": missing_keys,
    }


def check_subtotal(rows, total_key, component_keys, col, missing="fail"):
    """A printed section total equals the sum of its components.

    ``missing="fail"`` (default): any missing component fails the
    check. ``missing="zero"``: missing components contribute
    nothing, and their keys are listed in the detail — valid only
    where the missing value is a printed dash (stored as NULL),
    never for a genuinely missed extraction. Callers must record
    which keys were missing-as-zero.
    """
    total = _get(rows, total_key, col)
    if total is None:
        return False, {"reason": f"missing {total_key}"}
    acc = Decimal(0)
    missing_keys = []
    for key in component_keys:
        value = _get(rows, key, col)
        if value is None:
            missing_keys.append(key)
        else:
            acc += value
    if missing_keys and missing != "zero":
        return False, {"reason": "missing components", "keys": missing_keys}
    diff = total - acc
    return diff == 0, {
        "total": str(total),
        "computed": str(acc),
        "difference": str(diff),
        "missing_as_zero": missing_keys,
    }
