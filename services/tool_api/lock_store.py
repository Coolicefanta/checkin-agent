"""
内存锁存储 --- Phase 2 简易实现，Phase 6 替换为 Redis
"""
import threading
import time
import uuid


class LockStore:
    """内存锁存储，线程安全"""

    def __init__(self):
        self._locks: dict[str, dict] = {}
        self._lock = threading.Lock()

    def acquire(self, seat_id: str, ttl: int = 180) -> dict | None:
        """尝试锁定座位. 成功返回 {token, expires_at}, 失败返回 None"""
        now = time.time()
        with self._lock:
            # 清理过期锁
            for sid in list(self._locks.keys()):
                if self._locks[sid]["expires_at"] < now:
                    del self._locks[sid]

            if seat_id in self._locks:
                return None  # 已被锁定

            token = str(uuid.uuid4())
            expires_at = now + ttl
            self._locks[seat_id] = {"token": token, "expires_at": expires_at}
            return {"token": token, "expires_at": expires_at}

    def confirm(self, seat_id: str, token: str) -> bool:
        """确认锁定 (模拟, 实际在Phase 6写入DB)"""
        with self._lock:
            lock = self._locks.get(seat_id)
            if lock and lock["token"] == token and lock["expires_at"] > time.time():
                return True
            return False

    def release(self, seat_id: str, token: str) -> bool:
        """释放锁定"""
        with self._lock:
            lock = self._locks.get(seat_id)
            if lock and lock["token"] == token:
                del self._locks[seat_id]
                return True
            return False


# 全局单例
lock_store = LockStore()
