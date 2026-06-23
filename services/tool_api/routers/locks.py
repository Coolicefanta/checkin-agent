"""
锁路由 --- POST /locks/acquire, POST /locks/confirm, POST /locks/release
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.tool_api.lock_store import lock_store
from services.agent.config import settings

router = APIRouter(prefix="", tags=["locks"])

class AcquireRequest(BaseModel):
    seat_id: str
    ttl: int = settings.lock.ttl_seconds

class ConfirmRequest(BaseModel):
    seat_id: str
    token: str

class ReleaseRequest(BaseModel):
    seat_id: str
    token: str

@router.post("/locks/acquire")
async def acquire_lock(req: AcquireRequest):
    result = lock_store.acquire(req.seat_id, req.ttl)
    if result is None:
        raise HTTPException(status_code=409, detail="座位已被锁定")
    return {"seat_id": req.seat_id, **result}

@router.post("/locks/confirm")
async def confirm_lock(req: ConfirmRequest):
    return {"success": lock_store.confirm(req.seat_id, req.token)}

@router.post("/locks/release")
async def release_lock(req: ReleaseRequest):
    return {"success": lock_store.release(req.seat_id, req.token)}
