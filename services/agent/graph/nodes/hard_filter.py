from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from services.agent.graph.state import GraphState
from services.agent.recommendation.hard_filter import filter_seats
from shared.schemas import SeatStatus, SSEEvent, SSEEventType


async def hard_filter_node(state: GraphState) -> GraphState:
    seat_map: dict = state["seat_map"]  # type: ignore[assignment]
    if seat_map is None:
        return {**state, "status": "error", "next_action": "end"}

    total_rows: int = seat_map.get("rows", 0)

    # Stage 1: AVAILABLE only
    available = [s for s in seat_map["seats"] if s.get("status") == SeatStatus.AVAILABLE.value]

    # Stage 2: Apply deterministic hard constraints from state
    filtered_seats = filter_seats(
        available,
        wheelchair=state.get("wheelchair", False),
        motion_sickness=state.get("motion_sickness", False),
        companion_count=state.get("companion_count", 0),
        total_rows=total_rows,
    )

    filtered = {**seat_map, "seats": filtered_seats}

    events: list[SSEEvent] = list(state.get("sse_events", []))  # type: ignore[arg-type]
    events.append(SSEEvent(
        event_type=SSEEventType.PROGRESS,
        session_id=state["session_id"],
        data={
            "step": "hard_filter",
            "available_seats": len(filtered_seats),
            "constraints_applied": {
                "wheelchair": state.get("wheelchair", False),
                "motion_sickness": state.get("motion_sickness", False),
                "budget": state.get("budget"),
                "companion_count": state.get("companion_count", 0),
            },
        },
    ))

    return {**state, "seat_map": filtered, "sse_events": events, "next_action": "score"}
