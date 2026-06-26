"""事件路由 — GET /events/{user_id}?limit=20, POST /events"""
from __future__ import annotations

from fastapi import APIRouter, Query

from services.memory import episodic_store
from services.memory.schemas import EpisodicEvent

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/{user_id}")
async def get_events(user_id: str, limit: int = Query(default=20, ge=1, le=100)):
    events = episodic_store.events_by_user(user_id, limit=limit)
    return [e.model_dump(mode="json") for e in events]


@router.post("")
async def create_event(event: EpisodicEvent):
    stored = episodic_store.append_event(event)
    return stored.model_dump(mode="json")
