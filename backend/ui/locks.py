"""Per-manual locks shared by revision commits and run mutations, across processes."""

import fcntl
import threading
from contextlib import contextmanager
from functools import wraps
from pathlib import Path

_locks: dict[str, threading.RLock] = {}
_guard = threading.Lock()
_local = threading.local()


@contextmanager
def manual_lock(workspace: Path, manual_id: str):
    key = str(workspace.resolve() / manual_id)
    with _guard:
        lock = _locks.setdefault(key, threading.RLock())
    with lock:
        active = getattr(_local, "active", set())
        if key in active:
            yield
            return
        folder = workspace / ".locks"
        folder.mkdir(parents=True, exist_ok=True)
        import hashlib

        path = folder / (hashlib.sha256(key.encode()).hexdigest() + ".lock")
        with path.open("a") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                _local.active = active | {key}
                yield
            finally:
                _local.active = active
                fcntl.flock(handle, fcntl.LOCK_UN)


def locked_job(method):
    @wraps(method)
    def wrapped(self, manual_id, *args, **kwargs):
        self.catalog.manual_dir(manual_id)
        with manual_lock(self.workspace, manual_id):
            return method(self, manual_id, *args, **kwargs)

    return wrapped
