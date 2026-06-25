from __future__ import annotations


class LoopExhaustedError(Exception):
    def __init__(self, name: str, max_iterations: int) -> None:
        super().__init__(f"Loop '{name}' exhausted after {max_iterations} iterations")


class BoundedLoop:
    def __init__(self, max_iterations: int, name: str) -> None:
        self._max = max_iterations
        self._name = name
        self._count = 0

    def assert_progress(self) -> None:
        self._count += 1
        if self._count > self._max:
            raise LoopExhaustedError(self._name, self._max)

    def reset(self) -> None:
        self._count = 0
