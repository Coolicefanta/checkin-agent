"""
座位相关工具封装 --- agent 侧调用 tool_api REST 端点

原则: LLM 只能调 tool 获取数据，不能捏造 seat_id
"""
import httpx
from dataclasses import dataclass, field
from typing import Any, Callable

from services.agent.config import settings

TOOL_API_BASE = f"http://{settings.runtime.tool_api_host}:{settings.runtime.tool_api_port}"


@dataclass
class Tool:
    """简易工具定义 (替代 LangChain @tool)"""
    name: str
    description: str
    func: Callable
    parameters: dict = field(default_factory=dict)


def get_seat_map(voyage_id: str, cabin_class: str = "economy") -> dict:
    """获取航班/船班的座位图

    Args:
        voyage_id: 航班/船班ID, 如 'voyage_001'
        cabin_class: 舱位类型, 'economy' 或 'business'
    """
    resp = httpx.get(f"{TOOL_API_BASE}/seats/{voyage_id}", params={"cabin_class": cabin_class})
    resp.raise_for_status()
    return resp.json()


def get_order(order_id: str) -> dict:
    """获取订单信息

    Args:
        order_id: 订单ID
    """
    resp = httpx.get(f"{TOOL_API_BASE}/orders/{order_id}")
    resp.raise_for_status()
    return resp.json()


def temp_lock(seat_id: str, voyage_id: str) -> dict:
    """临时锁定座位

    Args:
        seat_id: 座位号, 如 '1A'
        voyage_id: 航班ID
    """
    resp = httpx.post(
        f"{TOOL_API_BASE}/locks/acquire",
        json={"seat_id": f"{voyage_id}-{seat_id}", "ttl": settings.lock.ttl_seconds},
    )
    resp.raise_for_status()
    return resp.json()


def get_weather(voyage_id: str) -> dict:
    """获取航班/船班的天气信息

    Args:
        voyage_id: 航班/船班ID
    """
    resp = httpx.get(f"{TOOL_API_BASE}/weather/{voyage_id}")
    resp.raise_for_status()
    return resp.json()


# 工具注册表
tool_registry = [
    Tool(name="get_seat_map", description="获取航班/船班的座位图",
         func=get_seat_map,
         parameters={"voyage_id": "string", "cabin_class": "string (optional, default economy)"}),
    Tool(name="get_order", description="获取订单信息",
         func=get_order,
         parameters={"order_id": "string"}),
    Tool(name="temp_lock", description="临时锁定座位",
         func=temp_lock,
         parameters={"seat_id": "string", "voyage_id": "string"}),
    Tool(name="get_weather", description="获取航班/船班的天气信息",
         func=get_weather,
         parameters={"voyage_id": "string"}),
]

__all__ = ["tool_registry", "Tool"]
