from __future__ import annotations

import os
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import yaml
from langchain_openai import ChatOpenAI

from services.agent.config import LLMProvider, settings
from services.agent.graph.state import GraphState
from shared.schemas import SSEEvent, SSEEventType


def _build_llm() -> ChatOpenAI:
    cfg = settings.llm
    kwargs: dict = dict(
        model=cfg.model,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        timeout=cfg.request_timeout,
        max_retries=cfg.max_retries,
    )
    if cfg.provider == LLMProvider.DEEPSEEK:
        kwargs["base_url"] = "https://api.deepseek.com"
        kwargs["api_key"] = os.environ.get("DEEPSEEK_API_KEY", "")
    return ChatOpenAI(**kwargs)


def _load_prompt() -> dict:
    path = settings.prompt_dir / "explanation.yaml"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


async def llm_explainer_node(state: GraphState) -> GraphState:
    reason_data: dict = state.get("reason_data") or {}  # type: ignore[attr-defined]
    prompt = _load_prompt()
    llm = _build_llm()
    order = state.get("order")
    passenger_name = order.user_id if order else "旅客"
    messages = [
        {"role": "system", "content": prompt["system"]},
        {
            "role": "user",
            "content": prompt["user_template"].format(
                passenger_name=passenger_name,
                seat_id=reason_data.get("seat_id", ""),
                seat_description=reason_data.get("seat_description", ""),
                matched_preferences=", ".join(reason_data.get("reasons", [])),
                score=reason_data.get("score", 0),
            ),
        },
    ]
    response = await llm.ainvoke(messages)
    explanation: str = response.content.strip()

    events: list[SSEEvent] = list(state.get("sse_events", []))  # type: ignore[arg-type]
    events.append(SSEEvent(
        event_type=SSEEventType.RECOMMENDATION,
        session_id=state["session_id"],
        data={"explanation": explanation, "seat_id": reason_data.get("seat_id")},
    ))
    return {
        **state,
        "sse_events": events,
        "status": "explained",
        "next_action": "lock",
    }
