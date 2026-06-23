"""
天气路由 --- GET /weather/{voyage_id}
"""
from fastapi import APIRouter, HTTPException
from services.tool_api.seed_data import get_weather, get_voyages

router = APIRouter(prefix="", tags=["weather"])


@router.get("/weather/{voyage_id}")
async def get_weather_endpoint(voyage_id: str):
    """获取航班天气"""
    voyages = {v["voyage_id"]: v for v in get_voyages()}
    if voyage_id not in voyages:
        raise HTTPException(status_code=404, detail="航班不存在")
    return get_weather(voyage_id)
