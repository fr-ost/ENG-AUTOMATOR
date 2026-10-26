from __future__ import annotations

import json
import os
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List


class StateError(RuntimeError):
    pass


@dataclass
class State:
    posts: List[Dict[str, Any]]
    last_successful_scan_at: str | None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "posts": self.posts,
            "last_successful_scan_at": self.last_successful_scan_at,
        }


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def default_state() -> State:
    return State(posts=[], last_successful_scan_at=None)


def validate_state(raw: Dict[str, Any]) -> State:
    if not isinstance(raw, dict):
        raise StateError("state must be an object")
    posts = raw.get("posts")
    if not isinstance(posts, list):
        raise StateError("state.posts must be a list")
    for index, post in enumerate(posts):
        if not isinstance(post, dict):
            raise StateError(f"state.posts[{index}] must be an object")
        if "post_id" not in post:
            raise StateError(f"state.posts[{index}] missing post_id")
    last_scan = raw.get("last_successful_scan_at")
    if last_scan is not None and not isinstance(last_scan, str):
        raise StateError("state.last_successful_scan_at must be null or string")
    return State(posts=posts, last_successful_scan_at=last_scan)


def load_state(path: Path, allow_recovery: bool = False) -> State:
    if not path.exists():
        return default_state()
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return validate_state(data)
    except (json.JSONDecodeError, OSError, StateError) as exc:
        if allow_recovery:
            broken_path = path.with_suffix(path.suffix + ".corrupt")
            path.replace(broken_path)
            return default_state()
        raise StateError(
            f"Failed to load state from {path}: {exc}. "
            "Use ALLOW_STATE_RECOVERY=true only after manually reviewing the file."
        ) from exc


def atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, sort_keys=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            tmp.write(payload)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_name, path)
    except OSError as exc:
        raise StateError(f"Failed to persist state atomically to {path}: {exc}") from exc
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def save_state(path: Path, state: State) -> None:
    validate_state(state.to_dict())
    atomic_write_json(path, state.to_dict())


@contextmanager
def file_lock(lock_path: Path) -> Iterator[None]:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise StateError(f"Another run appears active: lock file exists at {lock_path}") from exc
    try:
        os.write(fd, str(os.getpid()).encode("utf-8"))
        os.close(fd)
        yield
    finally:
        try:
            lock_path.unlink(missing_ok=True)
        except OSError:
            pass
