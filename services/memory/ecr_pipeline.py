"""ECR 管道 — Extract → Consolidate → Retrieve"""
from __future__ import annotations

import json
import os

import yaml
from langchain_openai import ChatOpenAI

from services.agent.config import LLMProvider, settings
from services.memory.schemas import SemanticProfile
from services.memory import episodic_store, semantic_store
from shared.schemas.preference import PreferenceCandidate

_VALID_PREF_KEYS = frozenset({"window", "aisle", "front", "rear", "away_from_toilet"})


def _build_llm() -> ChatOpenAI:
    """构建 LLM 客户端（复用 agent 侧逻辑）"""
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


def extract(session_id: str, user_input: str, profile: SemanticProfile | None = None) -> list[PreferenceCandidate]:
    """LLM 提取偏好 + 校验。

    校验规则：
    - key 必须是 5 个合法值之一
    - value ∈ [-1.0, 1.0]
    - confidence ∈ [0.0, 1.0]

    无证据时返回空列表（防止 LLM 幻觉污染记忆）。
    """
    try:
        prompt = _load_prompt()
        llm = _build_llm()
        messages = [
            {"role": "system", "content": prompt["system"]},
            {"role": "user", "content": prompt["user_template"].format(user_input=user_input)},
        ]
        response = llm.invoke(messages)
        raw: str = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        parsed: list[dict] = json.loads(raw)
    except Exception:
        return []

    candidates: list[PreferenceCandidate] = []
    for item in parsed:
        key = item.get("key", "")
        if key not in _VALID_PREF_KEYS:
            continue
        try:
            value = float(item.get("value", 0))
            confidence = float(item.get("confidence", 0))
        except (ValueError, TypeError):
            continue
        if not (-1.0 <= value <= 1.0):
            continue
        if not (0.0 <= confidence <= 1.0):
            continue
        if confidence == 0.0:
            continue
        candidates.append(PreferenceCandidate(
            key=key,
            value=value,
            confidence=confidence,
            evidence=user_input,
            session_id=session_id,
        ))

    return candidates


def consolidate(candidates: list[PreferenceCandidate], user_id: str) -> SemanticProfile:
    """确定性合并候选偏好到用户画像。

    对每个候选调用 semantic_store.apply_candidate。
    纠偏后旧记录标记 active=false（由 apply_candidate 内部处理）。
    """
    profile: SemanticProfile | None = None
    for c in candidates:
        profile = semantic_store.apply_candidate(user_id, c)
    if profile is None:
        profile = semantic_store.get_profile(user_id)
    return profile


def retrieve(user_id: str) -> SemanticProfile:
    """检索用户画像，冷启动返回默认"""
    return semantic_store.get_profile(user_id)


def run_ecr(session_id: str, user_input: str, user_id: str) -> SemanticProfile:
    """完整 ECR 管道：retrieve → extract → consolidate

    无证据时不写库（extract 返回空列表时跳过 consolidate）。
    """
    profile = retrieve(user_id)
    candidates = extract(session_id, user_input, profile)

    if not candidates:
        return profile

    # 存入情景记忆（append-only）
    from datetime import datetime
    from uuid import uuid4
    from services.memory.schemas import EpisodicEvent

    for c in candidates:
        event = EpisodicEvent(
            event_id=str(uuid4()),
            session_id=session_id,
            user_id=user_id,
            voyage_id="",
            event_type="preference_extraction",
            payload={"key": c.key, "value": c.value, "confidence": c.confidence},
            timestamp=datetime.utcnow(),
        )
        episodic_store.append_event(event)

    return consolidate(candidates, user_id)
