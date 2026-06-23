"""SSE事件模型---前后端共用类型定义"""
import time
from enum import Enum

from pydantic import BaseModel, Field


class SSEEventType(str, Enum):
    """SSE事件类型"""
    PREFERENCE_START = "preference_start"
    PREFERENCE_COMPLETE = "preference_complete"
    RECOMMENDATION = "recommendation"
    CONFLICT_CLARIFICATION = "conflict_clarification"
    PROGRESS = "progress"
    LOCKING = "locking"
    LOCK_CONFIRMED = "lock_confirmed"
    CHECKIN_COMPLETE = "checkin_complete"
    ERROR = "error"
    EXHAUSTED = "exhausted"


class SSEEvent(BaseModel):
    """SSE事件体"""
    event_type: SSEEventType
    session_id: str
    data: dict = Field(default_factory=dict, description="事件载荷")
    timestamp: float = Field(default_factory=time.time)
