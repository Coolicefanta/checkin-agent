"""
锁路由 --- POST /locks/acquire, POST /locks/confirm, POST /locks/release
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.tool_api.lock_store import lock_store

router = APIRouter(prefix="", tags=["locks"])


class AcquireRequest(BaseModel):
    seat_id: str
    ttl: int = 180


class ConfirmRequest(BaseModel):
    seat_id: str
    token: str


class ReleaseRequest(BaseModel):
    seat_id: str
    token: str


@router.post("/locks/acquire")
async def acquire_lock(req: AcquireRequest):
    """临时锁定座位"""
    result = lock_store.acquire(req.seat_id, req.ttl)
    if result is None:
        raise HTTPException(status_code=409, detail="座位已被锁定")
    return {"seat_id": req.seat_id, **result}


@router.post("/locks/confirm")
async def confirm_lock(req: ConfirmRequest):
    """确认锁定"""
    ok = lock_store.confirm(req.seat_id, req.token)
    return {"success": ok}


@router.post("/locks/release")
async def release_lock(req: ReleaseRequest):
    """释放锁定"""
    ok = lock_store.release(req.seat_id, req.token)
    return {"success": ok}
