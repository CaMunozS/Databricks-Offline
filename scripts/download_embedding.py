"""Download one Sentence Transformers model into a self-contained folder."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Hugging Face model identifier")
    parser.add_argument("--name", required=True, help="Local folder name")
    parser.add_argument("--revision", default=None, help="Optional Hugging Face revision")
    args = parser.parse_args()
    if not args.name or Path(args.name).name != args.name or args.name in {".", ".."}:
        print("ERROR: --name debe ser un nombre de carpeta simple.", file=sys.stderr)
        return 2
    destination = Path(__file__).resolve().parents[1] / "models" / "embeddings" / args.name
    if destination.exists():
        print(f"ERROR: el destino ya existe: {destination}", file=sys.stderr)
        return 2
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        print(f"ERROR: falta sentence-transformers: {exc}", file=sys.stderr)
        return 2
    try:
        model = SentenceTransformer(args.model, revision=args.revision) if args.revision else SentenceTransformer(args.model)
        destination.parent.mkdir(parents=True, exist_ok=True)
        model.save(str(destination), safe_serialization=True)
        metadata = {
            "name": args.name,
            "model_type": "embedding",
            "source": args.model,
            "revision": args.revision,
            "framework": "sentence-transformers",
            "python_target": "3.11",
            "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        (destination / "model-metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception as exc:
        print(f"ERROR: no se pudo preparar el modelo: {exc}", file=sys.stderr)
        return 1
    print(f"Modelo guardado en: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
