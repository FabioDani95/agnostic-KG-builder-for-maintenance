"""Content-addressed raw file store."""

from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from backend.security.boundary import contained_file

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CHUNK_SIZE = 1024 * 1024


def _configured_path(environment_key: str, fallback: str) -> Path:
    raw = str(os.environ.get(environment_key, "") or "").strip()
    if raw:
        path = Path(raw)
        return path if path.is_absolute() else (_REPO_ROOT / path).resolve()
    return (_REPO_ROOT / fallback).resolve()


def raw_root() -> Path:
    return _configured_path("KG_RAW_DIR", "data/raw")


def incoming_root() -> Path:
    return _configured_path("KG_INCOMING_DIR", "data/incoming")


@dataclass(frozen=True)
class StoredRaw:
    sha256: str
    size_bytes: int
    relative_path: str
    absolute_path: Path
    cache_hit: bool


class UploadTooLargeError(ValueError):
    pass


class RawStore:
    def __init__(self, root: Path | None = None, incoming: Path | None = None):
        self.root = (root or raw_root()).resolve()
        self.incoming = (incoming or incoming_root()).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.incoming.mkdir(parents=True, exist_ok=True)

    async def persist_upload(self, upload: UploadFile, *, max_bytes: int) -> StoredRaw:
        descriptor, temporary_name = tempfile.mkstemp(prefix="upload-", suffix=".part", dir=self.incoming)
        temporary = Path(temporary_name)
        digest = hashlib.sha256()
        size = 0
        try:
            with os.fdopen(descriptor, "wb") as handle:
                while True:
                    chunk = await upload.read(_CHUNK_SIZE)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > max_bytes:
                        raise UploadTooLargeError(f"Upload exceeds the configured limit of {max_bytes} bytes")
                    digest.update(chunk)
                    handle.write(chunk)
                handle.flush()
                os.fsync(handle.fileno())
            sha256 = digest.hexdigest()
            relative = Path(sha256[:2]) / sha256
            destination = (self.root / relative).resolve()
            destination.parent.mkdir(parents=True, exist_ok=True)
            cache_hit = destination.exists()
            if cache_hit:
                if not destination.is_file() or destination.is_symlink():
                    raise RuntimeError("Raw store entry is not a regular contained file")
                temporary.unlink(missing_ok=True)
            else:
                os.replace(temporary, destination)
            return StoredRaw(
                sha256=sha256,
                size_bytes=size,
                relative_path=relative.as_posix(),
                absolute_path=destination,
                cache_hit=cache_hit,
            )
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        finally:
            await upload.close()

    def resolve(self, relative_path: str) -> Path:
        path = Path(relative_path)
        if path.is_absolute():
            raise FileNotFoundError("Raw content reference must be inventory-relative")
        return contained_file(self.root, self.root / path)
