"""座位相关的 Pydantic 模型"""
from enum import Enum

from pydantic import BaseModel, Field


class SeatStatus(str, Enum):
    """座位状态"""
    AVAILABLE = "available"
    LOCKED = "locked"
    OCCUPIED = "occupied"


class CabinClass(str, Enum):
    """舱位类型"""
    FIRST = "first"
    BUSINESS = "business"
    ECONOMY = "economy"


class Seat(BaseModel):
    """单个座位"""
    seat_id: str = Field(..., description="座位唯一ID, 如'1A'")
    voyage_id: str = Field(..., description="所属航班/船班")
    cabin_class: CabinClass = Field(default=CabinClass.ECONOMY)
    row: int = Field(..., ge=1, description="排号")
    column: str = Field(..., description="列号 A/B/C/D/E/F")
    is_window: bool = Field(default=False, description="是否靠窗")
    is_aisle: bool = Field(default=False, description="是否过道")
    is_front: bool = Field(default=False, description="是否靠前(前1/3)")
    is_rear: bool = Field(default=False, description="是否靠后(后1/3)")
    near_toilet: bool = Field(default=False, description="是否靠近厕所")
    near_entrance: bool = Field(default=False, description="是否靠近入口")
    status: SeatStatus = Field(default=SeatStatus.AVAILABLE)
    price_multiplier: float = Field(default=1.0, ge=1.0, description="价格倍率(优选座位)")


class SeatMap(BaseModel):
    """整舱座位图"""
    voyage_id: str
    cabin_class: CabinClass
    seats: list[Seat] = Field(default_factory=list, description="所有座位")
    rows: int = Field(..., description="总排数")
    columns: list[str] = Field(default_factory=list, description="列字母列表")
