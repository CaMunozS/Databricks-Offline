"""Download one Sentence Transformers model into a self-contained folder."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


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
    staging = destination.parent / f".{args.name}.partial-{uuid4().hex}"
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        print(f"ERROR: falta sentence-transformers: {exc}", file=sys.stderr)
        return 2
    try:
        load_options = {"revision": args.revision} if args.revision else {}
        model = SentenceTransformer(args.model, trust_remote_code=False, **load_options)
        staging.mkdir(parents=True, exist_ok=False)
        model.save(str(staging), safe_serialization=True)
        metadata = {
            "name": args.name,
            "model_type": "embedding",
            "source": args.model,
            "revision": args.revision,
            "framework": "sentence-transformers",
            "python_target": "3.11",
            "downloaded_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        (staging / "model-metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        staging.replace(destination)
    except Exception as exc:
        if staging.exists():
            shutil.rmtree(staging)
        print(f"ERROR: no se pudo preparar el modelo: {exc}", file=sys.stderr)
        return 1
    print(f"Modelo guardado en: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
