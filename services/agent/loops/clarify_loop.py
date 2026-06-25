from services.agent.config import settings
from services.agent.loops.base import BoundedLoop


class ClarifyLoop(BoundedLoop):
    def __init__(self) -> None:
        super().__init__(settings.loop.clarify_max, "clarify")
