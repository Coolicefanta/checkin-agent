"""冷启动 — 默认群体先验 + 冷启动判定"""
from __future__ import annotations

from shared.schemas.preference import PreferenceItem, PreferenceSource

from services.memory.schemas import SemanticProfile


def is_cold_start(profile: SemanticProfile | None) -> bool:
    """判断是否冷启动：无 STATED 偏好且无高置信 EXTRACTED（confidence >= 0.7）"""
    if profile is None:
        return True
    return profile.is_cold_start()


def get_defaults(user_id: str) -> SemanticProfile:
    """返回默认群体先验画像 — window=0.5, aisle=0.3, front=0.2"""
    return SemanticProfile(
        user_id=user_id,
        preferences=[
            PreferenceItem(key="window", value=0.5, confidence=0.3, source=PreferenceSource.DEFAULT),
            PreferenceItem(key="aisle", value=0.3, confidence=0.3, source=PreferenceSource.DEFAULT),
            PreferenceItem(key="front", value=0.2, confidence=0.3, source=PreferenceSource.DEFAULT),
        ],
        version=0,
    )
