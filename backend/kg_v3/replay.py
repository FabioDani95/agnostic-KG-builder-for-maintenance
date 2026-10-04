"""Exact archived request replay. A cache miss has no path to the network."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace


def digest(value):
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def namespace(value):
    if isinstance(value, dict):
        return SimpleNamespace(**{k: namespace(v) for k, v in value.items()})
    if isinstance(value, list):
        return [namespace(v) for v in value]
    return value


class ReplayProvider:
    def __init__(self, directory: Path):
        self.responses = {}
        self.chat = SimpleNamespace(completions=self)
        self.calls = []
        for path in sorted(Path(directory).glob("*.json")):
            record = json.loads(path.read_text())
            if "request" in record and "response" in record:
                key = digest(record["request"])
                self.responses.setdefault(key, []).append(record)

    async def create(self, **kwargs):
        key = digest(kwargs)
        records = self.responses.get(key)
        if not records:
            raise ValueError(f"EXACT_REPLAY_MISS {key}; network fallback forbidden")
        self.calls.append(key)
        record = records.pop(0)
        if not record.get("response"):
            raise RuntimeError(f"archived provider failure: {record.get('error')}")
        return namespace(record["response"])
