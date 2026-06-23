"""
值机Agent --- FastAPI入口
提供6个REST端点, 启动时打印配置信息
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# 确保项目根目录在 sys.path 中
import sys
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from services.agent.config import settings

logger = logging.getLogger(__name__)


# === 6 个端点对应的占位处理函数 ===
# (后续阶段由LangGraph节点接管实际逻辑)


async def handle_checkin_start(data: dict) -> dict:
    """POST /checkin/start: 开始值机"""
    return {"session_id": "mock-session-id", "status": "started"}


async def handle_answer(session_id: str, data: dict) -> dict:
    """POST /{session_id}/answer: 回答澄清问题"""
    return {"session_id": session_id, "status": "answered"}


async def handle_stream(session_id: str) -> list[dict]:
    """GET /{session_id}/stream: SSE流(占位)"""
    return [{"event": "progress", "data": {"step": "mock"}}]


async def handle_confirm(session_id: str, data: dict) -> dict:
    """POST /{session_id}/confirm: 确认座位"""
    return {"session_id": session_id, "status": "confirmed"}


async def handle_next(session_id: str) -> dict:
    """POST /{session_id}/next: 换一个推荐"""
    return {"session_id": session_id, "status": "next"}


# === FastAPI应用 ===


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭生命周期"""
    logger.info("=" * 50)
    logger.info("值机Agent 服务启动")
    logger.info(f"  环境: {settings.runtime.env}")
    logger.info(f"  LLM模型: {settings.llm.provider.value}/{settings.llm.model}")
    logger.info(f"  Loop上限: A={settings.loop.repush_max} B={settings.loop.clarify_max} "
                f"C={settings.loop.reseat_max} D={settings.loop.tool_retry_max}")
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
async def stream(session_id: str):
    """SSE流(暂返回JSON占位)"""
    events = await handle_stream(session_id)
    return JSONResponse(content={"events": events})


@app.post("/{session_id}/confirm")
async def confirm(session_id: str, request: Request):
    """确认座位"""
    data = await request.json()
    result = await handle_confirm(session_id, data)
    return JSONResponse(content=result)


@app.post("/{session_id}/next")
async def next_recommendation(session_id: str, request: Request):
    """换一个推荐"""
    data = await request.json()
    result = await handle_next(session_id, data)
    return JSONResponse(content=result)


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}


# === main入口 ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.runtime.agent_host,
        port=settings.runtime.agent_port,
        reload=settings.runtime.debug,
    )
