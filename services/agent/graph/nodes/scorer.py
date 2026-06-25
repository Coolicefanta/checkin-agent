from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from services.agent.config import settings
from services.agent.graph.state import GraphState, to_preference_items
from services.agent.recommendation.scorer import score_seat
from shared.schemas import SSEEvent, SSEEventType


async def scorer_node(state: GraphState) -> GraphState:
    seat_map = state["seat_map"]  # type: ignore[assignment]
    preferences = to_preference_items(state)
    weights = {
        "window": settings.score.window_weight,
        "aisle": settings.score.aisle_weight,
        "front": settings.score.front_weight,
        "rear": settings.score.rear_weight,
        "away_from_toilet": settings.score.away_from_toilet_weight,
    }
    positive = sum(
        1 for seat in seat_map["seats"]
        if score_seat(seat if isinstance(seat, dict) else seat.model_dump(), preferences, weights) > 0.5
    )

    events: list[SSEEvent] = list(state.get("sse_events", []))  # type: ignore[arg-type]
    events.append(SSEEvent(
        event_type=SSEEventType.PROGRESS,
        session_id=state["session_id"],
        data={"step": "scorer", "positive_matches": positive},
    ))

    return {**state, "sse_events": events, "next_action": "detect_conflict"}
