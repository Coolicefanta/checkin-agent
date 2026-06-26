"""ECR 记忆系统 Pydantic 模型"""
from datetime import datetime

from pydantic import BaseModel, Field

from shared.schemas.preference import PreferenceItem


class EpisodicEvent(BaseModel):
    """情景记忆事件 — append-only"""
    event_id: str = Field(..., description="事件唯一ID")
    session_id: str = Field(..., description="会话ID")
    user_id: str = Field(..., description="用户ID")
    voyage_id: str = Field(..., description="航程ID")
    event_type: str = Field(..., description="事件类型: preference_extraction / user_feedback / clarification")
    payload: dict = Field(default_factory=dict, description="事件载荷")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="事件时间戳")


class SemanticProfile(BaseModel):
    """语义记忆画像 — 存储层模型（含 active 标志）"""
    user_id: str = Field(..., description="用户ID")
    preferences: list[PreferenceItem] = Field(default_factory=list, description="偏好列表")
    version: int = Field(default=1, description="画像版本号")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="最后更新时间")
    active: bool = Field(default=True, description="是否活跃（纠偏后旧记录标记 false）")

    def is_cold_start(self) -> bool:
        """是否冷启动: 无 STATED 偏好且无高置信 EXTRACTED（confidence >= 0.7）"""
        from shared.schemas.preference import PreferenceSource
        high_conf = [
            p for p in self.preferences
            if p.source in (PreferenceSource.STATED, PreferenceSource.EXTRACTED)
            and p.confidence >= 0.7
        ]
        return len(high_conf) == 0


class SessionContinuity(BaseModel):
    """会话连续性 — 程内顺延（去程→返程）"""
    user_id: str = Field(..., description="用户ID")
    previous_session_id: str = Field(..., description="上一个会话ID")
    previous_voyage_id: str = Field(..., description="上一个航程ID")
    continuity_type: str = Field(default="round_trip_outbound_to_return", description="顺延类型")
    carried_preferences: list[PreferenceItem] = Field(default_factory=list, description="携带的偏好")
