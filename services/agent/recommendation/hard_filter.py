"""Deterministic hard-constraint filter. Pure function — no LLM, no async, no HTTP.

Budget is NOT a hard constraint — it is handled in engine._detect_conflict() as PRICE_UPGRADE.
"""
from __future__ import annotations
import math


def filter_seats(
    seats: list[dict],
    *,
    wheelchair: bool = False,
    motion_sickness: bool = False,
    companion_count: int = 0,
    accessibility_pref_value: float = 0.0,
    total_rows: int = 0,
) -> list[dict]:
    """Apply 4 deterministic hard constraints, AND-ed. Skip constraints with no trigger."""
    result = seats

    # Constraint 1: Wheelchair → Aisle
    if wheelchair:
        result = [s for s in result if s.get("is_aisle")]

    # Constraint 2: Motion Sickness → Low-Motion Zone (front 30%)
    if motion_sickness and total_rows > 0:
        front_rows = max(1, math.ceil(total_rows * 0.3))
        result = [s for s in result if s.get("is_front") and s.get("row", 0) <= front_rows]

    # Constraint 3: Companion Grouping — sliding window for consecutive seats in same row
    if companion_count > 1:
        result = _filter_companion(result, companion_count)

    # Constraint 4: Accessibility (is_aisle AND near_entrance)
    if accessibility_pref_value > 0.5:
        result = [s for s in result if s.get("is_aisle") and s.get("near_entrance")]

    return result


def _filter_companion(seats: list[dict], companion_count: int) -> list[dict]:
    """Keep only seats that belong to a consecutive run of at least companion_count in the same row."""
    # Group seats by row
    by_row: dict[int, list[dict]] = {}
    for s in seats:
        by_row.setdefault(s["row"], []).append(s)

    valid_ids: set[str] = set()
    for row_seats in by_row.values():
        row_seats.sort(key=lambda s: s["column"])
        cols = [s["column"] for s in row_seats]
        col_map = {s["column"]: s["seat_id"] for s in row_seats}

        # Sliding window: check if each window of companion_count has consecutive columns
        col_order = _column_index
        indices = [col_order(c) for c in cols]

        for i in range(len(indices) - companion_count + 1):
            window_indices = indices[i : i + companion_count]
            if _is_consecutive(window_indices):
                for j in range(i, i + companion_count):
                    valid_ids.add(col_map[cols[j]])

    return [s for s in seats if s["seat_id"] in valid_ids]


def _column_index(col: str) -> int:
    """Map column letter to 0-based index (A=0, B=1, ...)."""
    return ord(col.upper()) - ord("A")


def _is_consecutive(indices: list[int]) -> bool:
    """Check if sorted indices form a consecutive run."""
    return all(indices[i] + 1 == indices[i + 1] for i in range(len(indices) - 1))
