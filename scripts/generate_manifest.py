"""Generate a per-model SHA-256 manifest."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    models = []
    for model_type in ("embeddings", "transformers"):
        base = ROOT / "models" / model_type
        folders = sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith(".")) if base.exists() else []
        for folder in folders:
            files = [{"path": path.relative_to(folder).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)} for path in sorted(p for p in folder.rglob("*") if p.is_file())]
            metadata_path = folder / "model-metadata.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
            models.append({"name": metadata.get("name", folder.name), "type": model_type[:-1], "relative_path": folder.relative_to(ROOT).as_posix(), "files": files})
    payload = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "python_target": "3.11", "models": models}
    target = ROOT / "model-manifest.json"
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Manifest generado: {target} ({len(models)} modelos)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
