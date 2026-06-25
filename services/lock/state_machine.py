from __future__ import annotations

from enum import Enum


class LockState(str, Enum):
    AVAILABLE = "available"
    LOCKED = "locked"
    CONFIRMED = "confirmed"
    OCCUPIED = "occupied"


class LockStateMachine:
    def __init__(self) -> None:
        self._states: dict[str, LockState] = {}

    def _get(self, seat_id: str) -> LockState:
        return self._states.get(seat_id, LockState.AVAILABLE)

    def _require(self, seat_id: str, expected: LockState) -> None:
        state = self._get(seat_id)
        if state != expected:
            raise ValueError(f"Seat {seat_id}: expected {expected.value}, got {state.value}")

    def acquire(self, seat_id: str) -> None:
        self._require(seat_id, LockState.AVAILABLE)
        self._states[seat_id] = LockState.LOCKED

    def confirm(self, seat_id: str) -> None:
        self._require(seat_id, LockState.LOCKED)
        self._states[seat_id] = LockState.CONFIRMED

    def release(self, seat_id: str) -> None:
        self._require(seat_id, LockState.LOCKED)
        self._states[seat_id] = LockState.AVAILABLE

    def occupy(self, seat_id: str) -> None:
        self._require(seat_id, LockState.CONFIRMED)
        self._states[seat_id] = LockState.OCCUPIED
