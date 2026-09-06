"""Reusable integrity checks for model folders."""
from __future__ import annotations

from pathlib import Path

LFS_POINTER_PREFIX = b"version https://git-lfs.github.com/spec/v1"


def is_lfs_pointer(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(len(LFS_POINTER_PREFIX)).startswith(LFS_POINTER_PREFIX)
    except OSError:
        return False


def lfs_pointers(model_dir: Path) -> list[Path]:
    return [path for path in model_dir.rglob("*") if path.is_file() and is_lfs_pointer(path)]


def looks_like_crlf_conversion(path: Path, expected_bytes: int) -> bool:
    actual_bytes = path.stat().st_size
    if actual_bytes <= expected_bytes:
        return False
    crlf_count = 0
    with path.open("rb") as handle:
        previous = b""
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            data = previous + block
            crlf_count += data.count(b"\r\n")
            previous = data[-1:]
    return actual_bytes - expected_bytes == crlf_count
