from __future__ import annotations

import asyncio
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import httpx

from services.agent.config import settings
from services.agent.graph.state import GraphState
from services.agent.loops.base import LoopExhaustedError
from services.agent.loops.tool_retry_loop import ToolRetryLoop
from shared.schemas import SSEEvent, SSEEventType

TOOL_API_BASE = f"http://{settings.runtime.tool_api_host}:{settings.runtime.tool_api_port}"


def _acquire_lock(seat_id: str, ttl: int) -> dict:
    """Acquire lock via Tool API, offloaded to thread."""
    resp = httpx.post(
        f"{TOOL_API_BASE}/locks/acquire",
        json={"seat_id": seat_id, "ttl": ttl},
    )
    resp.raise_for_status()
    return resp.json()


async def locker_node(state: GraphState) -> GraphState:
    recommendation = state["recommendation"]
    events: list[SSEEvent] = list(state.get("sse_events", []))  # type: ignore[arg-type]
    events.append(SSEEvent(
        event_type=SSEEventType.LOCKING,
        session_id=state["session_id"],
        data={"candidates": len(recommendation.candidates)},
    ))

    loop = ToolRetryLoop()
    lock_token: str | None = None
    loop_counters: dict[str, int] = dict(state.get("loop_counters", {}))  # type: ignore[arg-type]

    for candidate in recommendation.candidates:
        try:
            loop.assert_progress()
            result = await asyncio.to_thread(
                _acquire_lock, candidate.seat_id, settings.lock.ttl_seconds
            )
            lock_token = result.get("token")
            break
        except httpx.HTTPError:
            continue
        except LoopExhaustedError:
            break

    if lock_token:
        return {**state, "lock_token": lock_token, "sse_events": events, "status": "locked", "next_action": "complete"}

    # Reseat guard: increment counter, check against max
    loop_counters["reseat"] += 1
    if loop_counters["reseat"] >= settings.loop.reseat_max:
        events.append(SSEEvent(
            event_type=SSEEventType.EXHAUSTED,
            session_id=state["session_id"],
            data={"reason": "reseat_limit_reached"},
        ))
        return {**state, "sse_events": events, "loop_counters": loop_counters, "status": "exhausted", "next_action": "end"}

    return {**state, "sse_events": events, "loop_counters": loop_counters, "status": "reseating", "next_action": "reseat"}
