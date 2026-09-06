"""List locally available model folders and their metadata."""
from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1] / "models"
    rows: list[tuple[str, str, str, str, str]] = []
    for model_type in ("embeddings", "transformers"):
        base = root / model_type
        for folder in sorted(base.iterdir()) if base.exists() else []:
            metadata_path = folder / "model-metadata.json"
            if not folder.is_dir() or not metadata_path.exists():
                continue
            data = json.loads(metadata_path.read_text(encoding="utf-8"))
            rows.append((model_type[:-1], data.get("name", folder.name), data.get("source", ""), str(data.get("revision") or ""), data.get("framework", "")))
    print("type\tname\tsource\trevision\tframework")
    for row in rows:
        print("\t".join(row))
    print(f"Modelos encontrados: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
