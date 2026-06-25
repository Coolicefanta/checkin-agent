from services.agent.config import settings
from services.agent.loops.base import BoundedLoop


class ReseatLoop(BoundedLoop):
    def __init__(self) -> None:
        super().__init__(settings.loop.reseat_max, "reseat")
