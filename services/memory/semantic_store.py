"""语义记忆 — 用户画像存储 + 合并逻辑"""
from __future__ import annotations

from datetime import datetime

from shared.schemas.preference import PreferenceCandidate, PreferenceItem, PreferenceSource

from services.memory.cold_start import get_defaults
from services.memory.schemas import SemanticProfile

# 内存存储（预留 switch 到 PostgreSQL）
_profiles: dict[str, SemanticProfile] = {}
_profile_history: dict[str, list[SemanticProfile]] = {}  # 归档旧版本（纠偏审计）

_SOURCE_PRIORITY = {
    PreferenceSource.STATED: 3,
    PreferenceSource.EXTRACTED: 2,
    PreferenceSource.INFERRED: 1,
    PreferenceSource.DEFAULT: 0,
}


def _archive_profile(user_id: str, old_profile: SemanticProfile) -> None:
    """归档旧画像版本（纠偏审计）"""
    old_profile.active = False
    if user_id not in _profile_history:
        _profile_history[user_id] = []
    _profile_history[user_id].append(old_profile)


def get_profile(user_id: str) -> SemanticProfile:
    """获取用户画像，未找到时返回冷启动默认画像"""
    profile = _profiles.get(user_id)
    if profile is not None and profile.active:
        return profile
    return get_defaults(user_id)


def apply_candidate(user_id: str, candidate: PreferenceCandidate) -> SemanticProfile:
    """合并候选偏好到用户画像（同 key 加权平均，confidence 取 max，source 优先级: STATED > EXTRACTED > INFERRED）

    纠偏规则：当高优先级 source 覆盖低优先级时，归档旧画像（active=false），创建新版本。
    """
    old_profile = _profiles.get(user_id)
    is_existing = old_profile is not None and old_profile.active
    if is_existing:
        import copy
        profile = copy.deepcopy(old_profile)
    else:
        profile = get_defaults(user_id)

    existing_by_key: dict[str, PreferenceItem] = {p.key: p for p in profile.preferences}
    new_key = candidate.key
    needs_archive = False

    if new_key in existing_by_key:
        existing = existing_by_key[new_key]
        new_priority = _SOURCE_PRIORITY[PreferenceSource.EXTRACTED]
        old_priority = _SOURCE_PRIORITY.get(existing.source, 0)
        # 同 key 加权平均（无条件）
        total_weight = existing.confidence + candidate.confidence
        if total_weight > 0:
            existing.value = (existing.value * existing.confidence + candidate.value * candidate.confidence) / total_weight
        existing.confidence = max(existing.confidence, candidate.confidence)
        existing.timestamp = datetime.utcnow()
        if new_priority > old_priority:
            needs_archive = True
            existing.source = PreferenceSource.EXTRACTED
    else:
        new_item = PreferenceItem(
            key=candidate.key,
            value=candidate.value,
            confidence=candidate.confidence,
            source=PreferenceSource.EXTRACTED,
        )
        profile.preferences.append(new_item)

    profile.version += 1
    profile.updated_at = datetime.utcnow()

    if needs_archive and old_profile is not None:
        _archive_profile(user_id, old_profile)

    _profiles[user_id] = profile
    return profile


def stated_override(user_id: str, preferences: list[PreferenceItem]) -> SemanticProfile:
    """用户明确声明覆盖 — 直接覆盖对应 key，source 设为 STATED。纠偏时归档旧画像。"""
    import copy
    old_profile = _profiles.get(user_id)
    is_existing = old_profile is not None and old_profile.active
    if is_existing:
        profile = copy.deepcopy(old_profile)
    else:
        profile = get_defaults(user_id)

    override_keys = {p.key for p in preferences}
    kept = [p for p in profile.preferences if p.key not in override_keys]

    for p in preferences:
        kept.append(PreferenceItem(
            key=p.key,
            value=p.value,
            confidence=p.confidence,
            source=PreferenceSource.STATED,
        ))

    profile.preferences = kept
    profile.version += 1
    profile.updated_at = datetime.utcnow()

    if is_existing and old_profile is not None:
        _archive_profile(user_id, old_profile)

    _profiles[user_id] = profile
    return profile


def delete_profile(user_id: str) -> bool:
    """删除画像（GDPR）— 标记 active=False，不真删除"""
    profile = _profiles.get(user_id)
    if profile is None:
        return False
    profile.active = False
    profile.updated_at = datetime.utcnow()
    return True
