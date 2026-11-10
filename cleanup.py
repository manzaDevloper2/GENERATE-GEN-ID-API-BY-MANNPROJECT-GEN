"""
cleanup.py — Auto cleanup storage untuk Render.com
- Hapus file temp, cache, log lama
- Hapus file > N hari
- Hapus __pycache__ otomatis
- Trigger manual via /cleanup atau otomatis tiap interval
"""
import os
import shutil
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

CLEANUP_DIRS = [
    "/tmp",
    "/app/tmp",
    "/app/logs",
    "/app/cache",
    os.path.expanduser("~/.cache"),
]

CLEANUP_FILES = [
    "/app/nohup.out",
    "/app/debug.log",
    "/app/error.log",
]

CLEANUP_PATTERNS = [
    ".pyc", ".pyo", ".log", ".tmp", ".cache",
    ".zip", ".tar", ".gz", ".whl", ".egg",
]

CLEANUP_INTERVAL = int(os.getenv("CLEANUP_INTERVAL", "3600"))
MAX_STORAGE_MB   = int(os.getenv("MAX_STORAGE_MB", "400"))
MAX_AGE_DAYS     = int(os.getenv("MAX_AGE_DAYS", "3"))

_lock = threading.Lock()
_last_run = {"ts": None, "freed_mb": 0.0, "files_removed": 0, "status": "idle"}


def _dir_size_mb(path):
    total = 0
    try:
        for root, _, files in os.walk(path):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
    except OSError:
        pass
    return total / (1024 * 1024)


def _should_remove(file_path: Path):
    try:
        name = file_path.name.lower()
        if any(name.endswith(p) for p in CLEANUP_PATTERNS):
            return True
        mtime = file_path.stat().st_mtime
        age_days = (time.time() - mtime) / 86400
        if age_days > MAX_AGE_DAYS:
            return True
    except OSError:
        pass
    return False


def _remove_path(path: Path):
    try:
        if path.is_file() or path.is_symlink():
            sz = path.stat().st_size
            path.unlink()
            return sz
        elif path.is_dir():
            sz = int(_dir_size_mb(str(path)) * 1024 * 1024)
            shutil.rmtree(path, ignore_errors=True)
            return sz
    except OSError:
        pass
    return 0


def run_cleanup():
    global _last_run
    if not _lock.acquire(blocking=False):
        return {"skipped": True, "reason": "already running", **_last_run}
    try:
        freed_bytes = 0
        files_removed = 0

        for f in CLEANUP_FILES:
            p = Path(f)
            if p.exists():
                sz = _remove_path(p)
                if sz:
                    freed_bytes += sz
                    files_removed += 1

        for d in CLEANUP_DIRS:
            base = Path(d)
            if not base.exists():
                continue
            try:
                for item in base.iterdir():
                    if item.name in ("app", "node_modules", "venv", ".git", "site-packages"):
                        continue
                    if item.is_dir():
                        if any(k in item.name.lower() for k in ("cache", "tmp", "temp", "log", "pycache")):
                            sz = _remove_path(item)
                            if sz:
                                freed_bytes += sz
                                files_removed += 1
                    elif _should_remove(item):
                        sz = _remove_path(item)
                        if sz:
                            freed_bytes += sz
                            files_removed += 1
            except OSError:
                pass

        for root, dirs, _ in os.walk("/app"):
            for d in list(dirs):
                if d == "__pycache__":
                    p = Path(root) / d
                    sz = _remove_path(p)
                    if sz:
                        freed_bytes += sz
                        files_removed += 1
                    dirs.remove(d)

        total_mb = _dir_size_mb("/app") + _dir_size_mb("/tmp")
        if total_mb > MAX_STORAGE_MB:
            tmp_files = []
            for root, _, files in os.walk("/tmp"):
                for f in files:
                    p = Path(root) / f
                    try:
                        tmp_files.append((p, p.stat().st_size))
                    except OSError:
                        pass
            tmp_files.sort(key=lambda x: x[1], reverse=True)
            for p, sz in tmp_files:
                if total_mb <= MAX_STORAGE_MB:
                    break
                got = _remove_path(p)
                freed_bytes += got
                files_removed += 1
                total_mb -= got / (1024 * 1024)

        freed_mb = round(freed_bytes / (1024 * 1024), 2)
        _last_run = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "freed_mb": freed_mb,
            "files_removed": files_removed,
            "status": "success",
        }
        print(f"[cleanup] freed={freed_mb}MB, files={files_removed}")
        return _last_run
    except Exception as e:
        _last_run = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "freed_mb": 0.0,
            "files_removed": 0,
            "status": f"error: {e}",
        }
        return _last_run
    finally:
        _lock.release()


def start_cleanup_thread(interval=None):
    interval = interval or CLEANUP_INTERVAL

    def _loop():
        time.sleep(10)
        while True:
            try:
                run_cleanup()
            except Exception as e:
                print(f"[cleanup] thread error: {e}")
            time.sleep(interval)

    t = threading.Thread(target=_loop, daemon=True, name="auto-cleanup")
    t.start()
    print(f"[+] Cleanup thread started (interval={interval}s, max={MAX_STORAGE_MB}MB, age={MAX_AGE_DAYS}d)")
    return t


def get_cleanup_stats():
    with _lock:
        return dict(_last_run)