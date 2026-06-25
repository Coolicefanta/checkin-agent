from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from services.agent.graph.state import GraphState, to_preference_items
from services.agent.recommendation.engine import recommend
from shared.schemas import ConflictType, Seat, SeatMap, SSEEvent, SSEEventType


async def conflict_detector_node(state: GraphState) -> GraphState:
    seat_map = state["seat_map"]  # type: ignore[assignment]
    preferences = to_preference_items(state)
    prior = state.get("recommendation")
    cursor = prior.cursor if prior else 0

    seat_map_obj = SeatMap(
        voyage_id=seat_map["voyage_id"],
        cabin_class=seat_map["cabin_class"],
        seats=[Seat(**s) for s in seat_map["seats"]],
        rows=seat_map["rows"],
        columns=seat_map["columns"],
    )
    result = recommend(seat_map_obj, preferences, cursor=cursor)

    events: list[SSEEvent] = list(state.get("sse_events", []))  # type: ignore[arg-type]

    if result.conflict_type == ConflictType.NO_SUITABLE_SEAT or result.exhausted:
        next_action = "end"
        events.append(SSEEvent(
            event_type=SSEEventType.EXHAUSTED,
            session_id=state["session_id"],
            data={"reason": "no_suitable_seat"},
        ))
    elif result.conflict_type in (ConflictType.MULTIPLE_CANDIDATES, ConflictType.PRICE_UPGRADE):
        next_action = "clarify"
        events.append(SSEEvent(
            event_type=SSEEventType.CONFLICT_CLARIFICATION,
            session_id=state["session_id"],
            data={"conflict_type": result.conflict_type.value, "candidates": len(result.candidates)},
        ))
    else:
        next_action = "lock"
        seat_id = result.candidates[0].seat_id if result.candidates else None
        events.append(SSEEvent(
            event_type=SSEEventType.RECOMMENDATION,
            session_id=state["session_id"],
            data={"seat_id": seat_id},
        ))

    if result.conflict_type == ConflictType.NO_SUITABLE_SEAT or result.exhausted:
        status = "exhausted"
    elif result.conflict_type in (ConflictType.MULTIPLE_CANDIDATES, ConflictType.PRICE_UPGRADE):
        status = "clarifying"
    else:
        status = "recommended"

    return {
        **state,
        "recommendation": result,
        "sse_events": events,
        "status": status,
        "next_action": next_action,
    }
