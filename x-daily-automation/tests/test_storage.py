import json

import pytest

from src.storage import State, StateError, load_state, save_state


def test_load_missing_state_returns_default(tmp_path):
    state = load_state(tmp_path / "missing.json")
    assert state.posts == []
    assert state.last_successful_scan_at is None


def test_invalid_state_raises(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("{broken}", encoding="utf-8")
    with pytest.raises(StateError):
        load_state(path)


def test_atomic_save(tmp_path):
    path = tmp_path / "state.json"
    save_state(path, State(posts=[{"post_id": "1"}], last_successful_scan_at="2026-01-01T00:00:00Z"))
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["posts"][0]["post_id"] == "1"
