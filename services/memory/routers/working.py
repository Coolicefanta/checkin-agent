"""工作记忆路由 — GET /session/{session_id}, POST /session/{session_id}"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from services.memory import working_memory

router = APIRouter(prefix="/session", tags=["working"])


@router.get("/{session_id}")
async def get_session(session_id: str):
    session = working_memory.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/{session_id}")
async def save_session(session_id: str, data: dict):
    working_memory.set_session(session_id, data)
    return {"status": "ok", "session_id": session_id}
