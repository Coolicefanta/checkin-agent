"""Deterministic reason builder. Pure functions — no LLM, no async, no HTTP."""
from __future__ import annotations

from shared.schemas.preference import PreferenceItem
from shared.schemas.seat import Seat

_LABEL: dict[str, tuple[str | None, str]] = {
    "window": ("is_window", "靠窗"),
    "aisle": ("is_aisle", "靠过道"),
    "front": ("is_front", "靠前排"),
    "rear": ("is_rear", "靠后排"),
    "away_from_toilet": (None, "远离厕所"),
}


def build_reason(seat: Seat | dict, preferences: list[PreferenceItem]) -> list[str]:
    """Generate Chinese reason strings for why this seat matches user preferences."""
    reasons: list[str] = []
    for pref in preferences:
        if pref.value <= 0 or pref.key not in _LABEL:
            continue
        prop, label = _LABEL[pref.key]
        if pref.key == "away_from_toilet":
            near = seat.near_toilet if isinstance(seat, Seat) else seat.get("near_toilet", False)
            if not near:
                reasons.append(label)
        elif prop:
            match = getattr(seat, prop, False) if isinstance(seat, Seat) else seat.get(prop, False)
            if match:
                reasons.append(label)
    return reasons


def build_tradeoff_explanation(
    seat_a: Seat | dict,
    reasons_a: list[str],
    seat_b: Seat | dict,
    reasons_b: list[str],
) -> str:
    """Build a deterministic tradeoff explanation comparing two candidates."""
    a_id = seat_a.seat_id if isinstance(seat_a, Seat) else seat_a.get("seat_id", "未知")
    b_id = seat_b.seat_id if isinstance(seat_b, Seat) else seat_b.get("seat_id", "未知")
    a_reasons = "、".join(reasons_a) if reasons_a else "综合匹配"
    b_reasons = "、".join(reasons_b) if reasons_b else "综合匹配"
    return f"座位{a_id}满足：{a_reasons}；座位{b_id}满足：{b_reasons}。请根据偏好选择。"
