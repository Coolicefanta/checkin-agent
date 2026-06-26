"""画像路由 — GET /profile/{user_id}, POST /profile/{user_id}/apply, PUT /profile/{user_id}/override, DELETE /profile/{user_id}"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from services.memory import semantic_store
from shared.schemas.preference import PreferenceCandidate, PreferenceItem

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/{user_id}")
async def get_profile(user_id: str):
    profile = semantic_store.get_profile(user_id)
    return profile.model_dump(mode="json")


@router.post("/{user_id}/apply")
async def apply_candidate(user_id: str, candidate: PreferenceCandidate):
    profile = semantic_store.apply_candidate(user_id, candidate)
    return profile.model_dump(mode="json")


@router.put("/{user_id}/override")
async def override_preferences(user_id: str, preferences: list[PreferenceItem]):
    profile = semantic_store.stated_override(user_id, preferences)
    return profile.model_dump(mode="json")


@router.delete("/{user_id}")
async def delete_profile(user_id: str):
    ok = semantic_store.delete_profile(user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"status": "deleted", "user_id": user_id}
