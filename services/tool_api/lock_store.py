"""
内存锁存储 --- Phase 2 简易实现，Phase 6 替换为 Redis
"""
import threading, time, uuid

class LockStore:
    def __init__(self):
        self._locks: dict[str, dict] = {}
        self._lock = threading.Lock()

    def acquire(self, seat_id: str, ttl: int = 180) -> dict | None:
        now = time.time()
        with self._lock:
            for sid in list(self._locks.keys()):
                if self._locks[sid]["expires_at"] < now:
                    del self._locks[sid]
            if seat_id in self._locks:
                return None
            token = str(uuid.uuid4())
            self._locks[seat_id] = {"token": token, "expires_at": now + ttl}
            return {"token": token, "expires_at": now + ttl}

    def confirm(self, seat_id: str, token: str) -> bool:
        with self._lock:
            lock = self._locks.get(seat_id)
            return bool(lock and lock["token"] == token and lock["expires_at"] > time.time())

    def release(self, seat_id: str, token: str) -> bool:
        with self._lock:
            lock = self._locks.get(seat_id)
            if lock and lock["token"] == token:
                del self._locks[seat_id]
                return True
            return False

lock_store = LockStore()
