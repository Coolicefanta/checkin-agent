"""
订单路由 --- GET /orders/{order_id}
"""
from fastapi import APIRouter, HTTPException
from services.tool_api.seed_data import get_order

router = APIRouter(prefix="", tags=["orders"])


@router.get("/orders/{order_id}")
async def get_order_endpoint(order_id: str):
    """获取订单信息"""
    order = get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order
