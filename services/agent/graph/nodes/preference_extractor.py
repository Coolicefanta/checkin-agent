from __future__ import annotations

import json
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
from shared.schemas import PreferenceCandidate, SSEEvent, SSEEventType


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
    path = settings.prompt_dir / "preference_extraction.yaml"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


async def preference_extractor_node(state: GraphState) -> GraphState:
    session_id = state["session_id"]
    events: list[SSEEvent] = list(state.get("sse_events", []))  # type: ignore[arg-type]
    events.append(SSEEvent(
        event_type=SSEEventType.PREFERENCE_START,
        session_id=session_id,
        data={"step": "preference_extraction"},
    ))

    try:
        prompt = _load_prompt()
        llm = _build_llm()
        messages = [
            {"role": "system", "content": prompt["system"]},
            {"role": "user", "content": prompt["user_template"].format(user_input=state["user_input"])},
        ]
        response = await llm.ainvoke(messages)
        raw: str = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        parsed: list[dict] = json.loads(raw)
        candidates = [
            PreferenceCandidate(
                key=item["key"],
                value=float(item["value"]),
                confidence=float(item["confidence"]),
                evidence=state["user_input"],
                session_id=session_id,
            )
            for item in parsed
        ]
    except Exception as e:
        events.append(SSEEvent(
            event_type=SSEEventType.ERROR,
            session_id=session_id,
            data={"error": str(e)},
        ))
        return {
            **state,
            "sse_events": events,
            "error": str(e),
            "status": "error",
            "next_action": "end",
            "seat_map": {"seats": [], "voyage_id": "", "cabin_class": "economy", "rows": 0, "columns": []},
        }

    events.append(SSEEvent(
        event_type=SSEEventType.PREFERENCE_COMPLETE,
        session_id=session_id,
        data={"count": len(candidates)},
    ))

    return {
        **state,
        "extracted_preferences": candidates,
        "sse_events": events,
        "status": "preferences_extracted",
        "next_action": "recommend",
    }
