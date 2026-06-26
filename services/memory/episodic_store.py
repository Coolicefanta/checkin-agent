"""情景记忆 — append-only 事件存储"""
from __future__ import annotations

from services.memory.schemas import EpisodicEvent

# 内存存储（预留 switch 到 PostgreSQL）
_events: list[EpisodicEvent] = []


def append_event(event: EpisodicEvent) -> EpisodicEvent:
    """append-only 写入事件"""
    _events.append(event)
    return event


def events_by_session(session_id: str, limit: int = 50) -> list[EpisodicEvent]:
    """按会话查询事件"""
    return [e for e in _events if e.session_id == session_id][-limit:]


def events_by_user(user_id: str, limit: int = 20) -> list[EpisodicEvent]:
    """按用户查询事件"""
    return [e for e in _events if e.user_id == user_id][-limit:]


def events_by_pref(user_id: str, pref_key: str, limit: int = 20) -> list[EpisodicEvent]:
    """按偏好键查询事件 — 遍历 payload 中的 preference key"""
    result: list[EpisodicEvent] = []
    for e in reversed(_events):
        if e.user_id != user_id:
            continue
        payload = e.payload or {}
        if pref_key in payload:
            result.append(e)
        elif "key" in payload and payload.get("key") == pref_key:
            result.append(e)
        if len(result) >= limit:
            break
    result.reverse()
    return result


def anonymize_events(user_id: str) -> int:
    """匿名化用户事件（GDPR 合规）— 清除 user_id 并清空 payload"""
    count = 0
    for e in _events:
        if e.user_id == user_id:
            e.user_id = "anonymous"
            e.payload = {}
            count += 1
    return count
