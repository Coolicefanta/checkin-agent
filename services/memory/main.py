"""Memory 服务 FastAPI 入口 — 端口 8002"""
from __future__ import annotations

from fastapi import FastAPI

from services.memory.routers import events, profile, working

app = FastAPI(title="Checkin Memory API", version="0.1.0")

app.include_router(profile.router)
app.include_router(events.router)
app.include_router(working.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    print("Memory API starting on port 8002")
    uvicorn.run(app, host="0.0.0.0", port=8002)
