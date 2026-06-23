"""
座位路由 --- GET /seats/{voyage_id}
"""
from fastapi import APIRouter, HTTPException
from services.tool_api.seed_data import get_seats, get_voyages

router = APIRouter(prefix="", tags=["seats"])


@router.get("/seats/{voyage_id}")
async def get_seat_map(voyage_id: str, cabin_class: str = "economy"):
    """获取航班座位图"""
    # 验证 voyage_id 是否存在
    voyages = {v["voyage_id"]: v for v in get_voyages()}
    if voyage_id not in voyages:
        raise HTTPException(status_code=404, detail="航班不存在")

    seats = get_seats(voyage_id, cabin_class)
    v = voyages[voyage_id]

    return {
        "voyage_id": voyage_id,
        "cabin_class": cabin_class,
        "seats": seats,
        "rows": 10,
        "columns": ["A", "B", "C", "D", "E", "F"],
    }
