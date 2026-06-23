"""
Tool API 服务 --- Mock 数据 REST 端点
提供订单查询、座位图、天气、锁操作等接口
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from services.tool_api.routers.orders import router as orders_router
from services.tool_api.routers.seats import router as seats_router
from services.tool_api.routers.weather import router as weather_router
from services.tool_api.routers.locks import router as locks_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="值机Agent Tool API",
    description="Mock 数据服务",
    version="0.1.0",
)

app.include_router(orders_router)
app.include_router(seats_router)
app.include_router(weather_router)
app.include_router(locks_router)


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
