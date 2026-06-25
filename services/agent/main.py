"""
值机Agent --- FastAPI入口
提供6个REST端点, 启动时打印配置信息
Phase 3: 真实LangGraph图替换占位处理器
"""
from __future__ import annotations

import json
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

# 确保项目根目录在 sys.path 中
import sys

_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from services.agent.config import settings
from services.agent.graph.graph import build_graph
from services.agent.graph.state import GraphState

logger = logging.getLogger(__name__)

# 构建LangGraph图（模块级单例）
agent_graph = build_graph()

# 会话存储（内存，Phase 6 迁移到 Redis）
sessions: dict[str, GraphState] = {}


# === 6 个端点处理函数 ===


async def handle_checkin_start(data: dict) -> dict:
    """POST /checkin/start: 开始值机"""
    session_id = str(uuid.uuid4())
    order_id = data.get("order_id", "unknown")
    user_input = data.get("user_input", "")

    initial_state: GraphState = {
        "session_id": session_id,
        "order_id": order_id,
        "order": None,
        "checkin_context": None,
        "user_input": user_input,
        "user_profile": None,
        "extracted_preferences": [],
        "seat_map": None,
        "recommendation": None,
        "lock_token": None,
        "sse_events": [],
        "loop_counters": {"repush": 0, "clarify": 0, "reseat": 0, "tool_retry": 0},
        "error": None,
        "reason_data": None,
        "status": "started",
        "next_action": "retrieve_context",
    }

    logger.info(f"开始值机 session={session_id} order={order_id}")
    try:
        result = await agent_graph.ainvoke(initial_state)
    except Exception as e:
        logger.error(f"Graph invocation failed session={session_id}: {e}")
        return {"session_id": session_id, "status": "error", "error": str(e)}
    sessions[session_id] = result

    return {
        "session_id": session_id,
        "status": result.get("status", "started"),
        "next_action": result.get("next_action", ""),
    }


async def handle_answer(session_id: str, data: dict) -> dict:
    """POST /{session_id}/answer: 回答澄清问题"""
    state = sessions.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")

    state["user_input"] = data.get("answer", "")
    state["next_action"] = "extract_preferences"
    state["status"] = "started"

    logger.info(f"用户回答 session={session_id}")
    try:
        result = await agent_graph.ainvoke(state)
    except Exception as e:
        logger.error(f"Graph invocation failed session={session_id}: {e}")
        return {"session_id": session_id, "status": "error", "error": str(e)}
    sessions[session_id] = result

    return {
        "session_id": session_id,
        "status": result.get("status", "started"),
        "next_action": result.get("next_action", ""),
    }


async def handle_stream(session_id: str) -> EventSourceResponse:
    """GET /{session_id}/stream: SSE流"""
    state = sessions.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_generator():
        for event in state.get("sse_events", []):
            event_data = {
                "event": event.event_type.value,
                "data": json.dumps(event.data, ensure_ascii=False),
            }
            yield event_data

    return EventSourceResponse(event_generator())


async def handle_confirm(session_id: str, data: dict) -> dict:
    """POST /{session_id}/confirm: 确认座位"""
    state = sessions.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")

    state["next_action"] = "lock"
    state["status"] = "recommended"

    logger.info(f"用户确认座位 session={session_id}")
    result = await agent_graph.ainvoke(state)
    sessions[session_id] = result

    return {
        "session_id": session_id,
        "status": result.get("status", "started"),
        "recommendation": (
            result["recommendation"].model_dump()
            if result.get("recommendation")
            else None
        ),
    }


async def handle_next(session_id: str) -> dict:
    """POST /{session_id}/next: 换一个推荐"""
    state = sessions.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # 增量重推计数器
    state["loop_counters"]["repush"] += 1
    if state["loop_counters"]["repush"] >= settings.loop.repush_max:
        state["status"] = "exhausted"
        sessions[session_id] = state
        return {"session_id": session_id, "status": "exhausted", "message": "重推次数已达上限"}

    # 推进游标
    if state.get("recommendation") is not None:
        state["recommendation"].cursor += 3

    state["next_action"] = "recommend"
    state["status"] = "started"

    logger.info(f"用户换座 session={session_id} repush={state['loop_counters']['repush']}")
    result = await agent_graph.ainvoke(state)
    sessions[session_id] = result

    return {
        "session_id": session_id,
        "status": result.get("status", "started"),
        "recommendation": (
            result["recommendation"].model_dump()
            if result.get("recommendation")
            else None
        ),
    }


# === FastAPI应用 ===


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭生命周期"""
    logger.info("=" * 50)
    logger.info("值机Agent 服务启动")
    logger.info(f"  环境: {settings.runtime.env}")
    logger.info(f"  LLM模型: {settings.llm.provider.value}/{settings.llm.model}")
    logger.info(
        f"  Loop上限: A={settings.loop.repush_max} B={settings.loop.clarify_max} "
        f"C={settings.loop.reseat_max} D={settings.loop.tool_retry_max}"
    )
    logger.info(f"  锁TTL: {settings.lock.ttl_seconds}s")
    logger.info(f"  项目根: {settings.project_root}")
    logger.info("=" * 50)
    yield
    logger.info("值机Agent 服务关闭")


app = FastAPI(
    title="值机Agent",
    description="抚远购票智能值机系统",
    version="0.1.0",
    lifespan=lifespan,
)


@app.post("/checkin/start")
async def checkin_start(request: Request):
    """开始值机"""
    data = await request.json()
    result = await handle_checkin_start(data)
    return JSONResponse(content=result)


@app.post("/{session_id}/answer")
async def answer(session_id: str, request: Request):
    """回答澄清问题"""
    data = await request.json()
    result = await handle_answer(session_id, data)
    return JSONResponse(content=result)


@app.get("/{session_id}/stream")
async def stream(session_id: str, request: Request):
    """SSE流"""
    return await handle_stream(session_id)


@app.post("/{session_id}/confirm")
async def confirm(session_id: str, request: Request):
    """确认座位"""
    data = await request.json()
    result = await handle_confirm(session_id, data)
    return JSONResponse(content=result)


@app.post("/{session_id}/next")
async def next_recommendation(session_id: str, request: Request):
    """换一个推荐"""
    result = await handle_next(session_id)
    return JSONResponse(content=result)


@app.get("/health")
async def health():
    return {"status": "ok", "graphs": 1, "active_sessions": len(sessions)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.runtime.agent_host, port=settings.runtime.agent_port, reload=settings.runtime.debug)