"""推荐相关的 Pydantic 模型 --- 同时充当tool API的输入输出契约"""
from enum import Enum

from pydantic import BaseModel, Field


class ConflictType(str, Enum):
    """冲突类型"""
    NO_CONFLICT = "no_conflict"
    PRICE_UPGRADE = "price_upgrade"
    PREFERENCE_TRADEOFF = "preference_tradeoff"
    MULTIPLE_CANDIDATES = "multiple_candidates"
    NO_SUITABLE_SEAT = "no_suitable_seat"


class ConflictResolution(str, Enum):
    """冲突决策"""
    PROCEED = "proceed"
    ASK_USER = "ask_user"
    AUTO_RESOLVE = "auto_resolve"


class RecommendedSeat(BaseModel):
    """单条推荐座位"""
    seat_id: str
    row: int
    column: str
    cabin_class: str = "economy"
    score: float = Field(..., ge=0.0, le=1.0, description="推荐分0~1")
    reasons: list[str] = Field(default_factory=list, description="推荐理由(确定性生成)")
    price_multiplier: float = Field(default=1.0)


class RecommendationResult(BaseModel):
    """推荐引擎输出---同时也是tool api的契约"""
    voyage_id: str
    candidates: list[RecommendedSeat] = Field(default_factory=list)
    conflict_type: ConflictType = ConflictType.NO_CONFLICT
    conflict_resolution: ConflictResolution = ConflictResolution.PROCEED
    conflict_detail: str = Field(default="", description="冲突描述(如需ask_user)")
    exhausted: bool = Field(default=False, description="游标是否耗尽")
    cursor: int = Field(default=0, ge=0, description="当前候选游标位置")
