from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from services.agent.graph.state import GraphState
from shared.schemas import SSEEvent, SSEEventType


async def checkin_completer_node(state: GraphState) -> GraphState:
    recommendation = state.get("recommendation")
    top = recommendation.candidates[0] if recommendation and recommendation.candidates else None
    events: list[SSEEvent] = list(state.get("sse_events", []))  # type: ignore[arg-type]
    events.append(SSEEvent(
        event_type=SSEEventType.CHECKIN_COMPLETE,
        session_id=state["session_id"],
        data={
            "lock_token": state.get("lock_token"),
            "seat_id": top.seat_id if top else None,
        },
    ))
    return {**state, "sse_events": events, "status": "completed", "next_action": "end"}
