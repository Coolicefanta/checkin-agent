from services.agent.config import settings
from services.agent.loops.base import BoundedLoop


class ToolRetryLoop(BoundedLoop):
    def __init__(self) -> None:
        super().__init__(settings.loop.tool_retry_max, "tool_retry")
