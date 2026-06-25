from services.agent.config import settings
from services.agent.loops.base import BoundedLoop


class RepushLoop(BoundedLoop):
    def __init__(self) -> None:
        super().__init__(settings.loop.repush_max, "repush")
