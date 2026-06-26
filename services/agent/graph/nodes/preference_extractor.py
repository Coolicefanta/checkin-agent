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

    # Fire-and-forget: persist to memory API (non-blocking)
    import asyncio
    user_id = state.get("user_profile", {}).get("user_id", session_id) if isinstance(state.get("user_profile"), dict) else session_id
    voyage_id = state.get("order", {}).get("voyage_id", "") if isinstance(state.get("order"), dict) else ""
    asyncio.create_task(_persist_to_memory(session_id, user_id, voyage_id, candidates, state["user_input"]))

    return {
        **state,
        "extracted_preferences": candidates,
        "sse_events": events,
        "status": "preferences_extracted",
        "next_action": "recommend",
    }


async def _persist_to_memory(
    session_id: str,
    user_id: str,
    voyage_id: str,
    candidates: list[PreferenceCandidate],
    user_input: str,
) -> None:
    """Persist extracted preferences to Memory API (fire-and-forget, non-blocking)."""
    try:
        import httpx
        memory_host = settings.runtime.memory_api_host
        memory_port = settings.runtime.memory_api_port
        base = f"http://{memory_host}:{memory_port}"

        async with httpx.AsyncClient(timeout=5.0) as client:
            # POST /events — store episodic event
            from uuid import uuid4
            from datetime import datetime
            await client.post(f"{base}/events", json={
                "event_id": str(uuid4()),
                "session_id": session_id,
                "user_id": user_id,
                "voyage_id": voyage_id,
                "event_type": "preference_extracted",
                "payload": {
                    "candidates": [c.model_dump() for c in candidates],
                    "user_input": user_input,
                },
                "timestamp": datetime.utcnow().isoformat(),
            })
            # POST /profile/{user_id}/apply — update semantic memory
            for c in candidates:
                await client.post(f"{base}/profile/{user_id}/apply", json={
                    "key": c.key,
                    "value": c.value,
                    "confidence": c.confidence,
                    "evidence": c.evidence,
                    "session_id": session_id,
                })
    except Exception:
        # Memory API is unavailable — graceful degradation, don't block main flow
        pass
