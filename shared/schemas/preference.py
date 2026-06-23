"""偏好相关的 Pydantic 模型"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PreferenceSource(str, Enum):
    """偏好来源"""
    STATED = "stated"
    EXTRACTED = "extracted"
    INFERRED = "inferred"
    DEFAULT = "default"


class PreferenceItem(BaseModel):
    """单条偏好"""
    key: str = Field(..., description="偏好键, 如'window', 'aisle', 'front'")
    value: float = Field(..., ge=-1.0, le=1.0, description="偏好值 -1(讨厌)~1(喜欢)")
    source: PreferenceSource = Field(default=PreferenceSource.STATED)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="置信度")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UserProfile(BaseModel):
    """用户画像(语义记忆)"""
    user_id: str
    preferences: list[PreferenceItem] = Field(default_factory=list)
    version: int = Field(default=1, description="画像版本号")
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def is_cold_start(self) -> bool:
        """是否冷启动: 无STATED偏好且无高置信EXTRACTED"""
        high_conf = [
            p for p in self.preferences
            if p.source in (PreferenceSource.STATED, PreferenceSource.EXTRACTED)
            and p.confidence >= 0.7
        ]
        return len(high_conf) == 0


class PreferenceCandidate(BaseModel):
    """ECR管道提取的候选偏好(待consolidate确认)"""
    key: str
    value: float
    confidence: float
    evidence: str = Field(..., description="证据文本片段")
    session_id: str
