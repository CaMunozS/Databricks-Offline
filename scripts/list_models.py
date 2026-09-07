"""List locally available model folders and their metadata."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1] / "models"
    count = 0
    for model_type, label in (("embeddings", "EMBEDDINGS"), ("transformers", "TRANSFORMERS"), ("spacy", "SPACY"), ("libs", "LIBS")):
        print(label)
        base = root / model_type
        for folder in sorted(base.iterdir()) if base.exists() else []:
            metadata_path = folder / "model-metadata.json"
            if not folder.is_dir() or folder.name.startswith("."):
                continue
            if not metadata_path.exists():
                print(f"- {folder.name} (ERROR: falta model-metadata.json)", file=sys.stderr)
                continue
            try:
                data = json.loads(metadata_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                print(f"- {folder.name} (ERROR: metadata JSON inválida: {exc})", file=sys.stderr)
                continue
            print(f"- nombre: {data.get('name', folder.name)}")
            print(f"  source: {data.get('source', '')}")
            print(f"  revision: {data.get('revision') or ''}")
            print(f"  framework: {data.get('framework', '')}")
            print(f"  license: {data.get('license', '')}")
            print(f"  validation notebook: {'OK' if (folder / 'validation.ipynb').is_file() else 'MISSING'}")
            count += 1
        print()
    print(f"{count} modelos disponibles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
