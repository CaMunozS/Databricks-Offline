"""Verify a Unity Catalog Volume model copy against model-manifest.json."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--volume-root", type=Path, required=True, help="/Volumes/<catalog>/<schema>/<volume>")
    parser.add_argument("--manifest", type=Path, default=ROOT / "model-manifest.json")
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: no se pudo leer el manifest: {exc}", file=sys.stderr)
        return 2
    failures: list[str] = []
    verified = 0
    for model in manifest.get("models", []):
        folder = args.volume_root / model["relative_path"]
        for item in model.get("files", []):
            path = folder / item["path"]
            if not path.is_file():
                failures.append(f"faltante: {path}")
            elif path.stat().st_size != item["bytes"]:
                failures.append(f"tamaño incorrecto: {path}")
            elif sha256(path) != item["sha256"]:
                failures.append(f"SHA-256 incorrecto: {path}")
            else:
                verified += 1
    if failures:
        print("VOLUME VERIFY FAILED")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1
    print(f"VOLUME VERIFY OK: {verified} archivos verificados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
