from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from typing import TypedDict

from shared.schemas import (
    CheckinContext,
    Order,
    PreferenceCandidate,
    PreferenceItem,
    PreferenceSource,
    RecommendationResult,
    SSEEvent,
    UserProfile,
)


class GraphState(TypedDict):
    session_id: str
    order_id: str
    order: Order | None
    checkin_context: CheckinContext | None
    user_input: str
    user_profile: UserProfile | None
    extracted_preferences: list[PreferenceCandidate]
    seat_map: dict | None
    recommendation: RecommendationResult | None
    lock_token: str | None
    sse_events: list[SSEEvent]
    loop_counters: dict[str, int]
    error: str | None
    reason_data: dict | None
    status: str
    next_action: str
    # Hard constraint params for recommendation engine
    wheelchair: bool
    motion_sickness: bool
    budget: float | None
    companion_count: int


def to_preference_items(state: GraphState) -> list[PreferenceItem]:
    candidates = state.get("extracted_preferences") or []
    if candidates:
        return [
            PreferenceItem(key=c.key, value=c.value, confidence=c.confidence, source=PreferenceSource.EXTRACTED)
            for c in candidates
        ]
    profile = state.get("user_profile")
    return profile.preferences if profile else []
