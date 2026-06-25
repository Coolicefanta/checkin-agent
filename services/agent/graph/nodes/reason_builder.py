from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from services.agent.graph.state import GraphState


async def reason_builder_node(state: GraphState) -> GraphState:
    recommendation = state["recommendation"]
    top = recommendation.candidates[0] if recommendation and recommendation.candidates else None
    reason_data: dict = {}
    if top:
        reason_data = {
            "seat_id": top.seat_id,
            "row": top.row,
            "column": top.column,
            "cabin_class": top.cabin_class,
            "score": top.score,
            "reasons": top.reasons,
            "seat_description": f"{top.row}排{top.column}座（{top.cabin_class}舱）",
        }
    return {
        **state,
        "reason_data": reason_data,  # type: ignore[typeddict-unknown-key]
        "next_action": "explain",
    }
