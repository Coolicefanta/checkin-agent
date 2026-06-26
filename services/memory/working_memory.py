"""工作记忆 — 会话状态存储 + 程内顺延"""
from __future__ import annotations

from services.memory.schemas import SessionContinuity

# 内存存储（预留 switch 到 Redis）
_sessions: dict[str, dict] = {}
_continuities: dict[str, SessionContinuity] = {}


def get_session(session_id: str) -> dict | None:
    """获取当前会话状态"""
    return _sessions.get(session_id)


def set_session(session_id: str, data: dict) -> dict:
    """保存会话状态（全量覆盖）"""
    _sessions[session_id] = data
    return data


def patch_session(session_id: str, patch: dict) -> dict:
    """增量更新会话状态"""
    current = _sessions.get(session_id, {})
    current.update(patch)
    _sessions[session_id] = current
    return current


def get_continuity(user_id: str) -> SessionContinuity | None:
    """获取程内顺延（去程→返程）"""
    return _continuities.get(user_id)


def set_continuity(user_id: str, continuity: SessionContinuity) -> SessionContinuity:
    """设置程内顺延"""
    _continuities[user_id] = continuity
    return continuity
