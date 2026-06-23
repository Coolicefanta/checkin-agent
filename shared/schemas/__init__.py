"""
统一导出所有数据模型
"""
from shared.schemas.order import Order, CheckinContext, OrderStatus, VoyageInfo
from shared.schemas.seat import Seat, SeatStatus, CabinClass, SeatMap
from shared.schemas.preference import (
    PreferenceItem, PreferenceSource, UserProfile, PreferenceCandidate,
)
from shared.schemas.recommendation import (
    RecommendedSeat, RecommendationResult, ConflictType, ConflictResolution,
)
from shared.schemas.sse_events import SSEEvent, SSEEventType

__all__ = [
    "Order", "CheckinContext", "OrderStatus", "VoyageInfo",
    "Seat", "SeatStatus", "CabinClass", "SeatMap",
    "PreferenceItem", "PreferenceSource", "UserProfile", "PreferenceCandidate",
    "RecommendedSeat", "RecommendationResult", "ConflictType", "ConflictResolution",
    "SSEEvent", "SSEEventType",
]
