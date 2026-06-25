from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from services.agent.graph.state import GraphState
from shared.schemas import SeatStatus, SSEEvent, SSEEventType


async def hard_filter_node(state: GraphState) -> GraphState:
    seat_map: dict = state["seat_map"]  # type: ignore[assignment]
    if seat_map is None:
        return {**state, "status": "error", "next_action": "end"}
    available = [s for s in seat_map["seats"] if s["status"] == SeatStatus.AVAILABLE]
    filtered = {**seat_map, "seats": available}

    events: list[SSEEvent] = list(state.get("sse_events", []))  # type: ignore[arg-type]
    events.append(SSEEvent(
        event_type=SSEEventType.PROGRESS,
        session_id=state["session_id"],
        data={"step": "hard_filter", "available_seats": len(available)},
    ))

    return {**state, "seat_map": filtered, "sse_events": events, "next_action": "score"}
