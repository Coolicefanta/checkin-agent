from __future__ import annotations

import asyncio
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from services.agent.graph.state import GraphState
from services.agent.tools.seat_tools import get_order, get_seat_map
from shared.schemas import Order, SSEEvent, SSEEventType


async def retrieve_context_node(state: GraphState) -> GraphState:
    order_id = state.get("order_id", "")
    events: list[SSEEvent] = list(state.get("sse_events", []))  # type: ignore[arg-type]
    try:
        order_data = await asyncio.to_thread(get_order, order_id)
        order = Order(**order_data)
        voyage_id = order.voyage.voyage_id
        cabin_class = order.voyage.cabin_class
        seat_map = await asyncio.to_thread(get_seat_map, voyage_id, cabin_class)
    except Exception as e:
        return {**state, "status": "error", "next_action": "end", "error": str(e), "sse_events": events}

    events.append(SSEEvent(
        event_type=SSEEventType.PROGRESS,
        session_id=state["session_id"],
        data={"step": "retrieve_context", "voyage_id": voyage_id},
    ))
    return {**state, "order": order, "seat_map": seat_map, "sse_events": events, "next_action": "extract_preferences"}
