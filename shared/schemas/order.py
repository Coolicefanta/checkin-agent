"""订单相关的 Pydantic 模型"""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    """订单状态"""
    PENDING = "pending"
    CHECKED_IN = "checked_in"
    CANCELLED = "cancelled"


class VoyageInfo(BaseModel):
    """航班/船班信息"""
    voyage_id: str = Field(..., description="航班/船班唯一ID")
    route_name: str = Field(..., description="航线名称, 如'抚远→黑瞎子岛'")
    departure_port: str = Field(..., description="出发港口/码头")
    arrival_port: str = Field(..., description="到达港口/码头")
    departure_time: datetime = Field(..., description="出发时间")
    arrival_time: datetime = Field(..., description="到达时间")
    cabin_class: str = Field(default="economy", description="舱位")


class Order(BaseModel):
    """订单"""
    order_id: str = Field(..., description="订单唯一ID")
    user_id: str = Field(..., description="用户ID")
    voyage: VoyageInfo = Field(..., description="航班/船班信息")
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    seat_number: Optional[str] = Field(default=None, description="已选座位号")


class CheckinContext(BaseModel):
    """值机会话上下文, 存在Redis中"""
    session_id: str
    order_id: str
    user_id: str
    current_step: str = "start"
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
