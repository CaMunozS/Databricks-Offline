"""Download one Transformers model and tokenizer into a self-contained folder."""
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
    destination = Path(__file__).resolve().parents[1] / "models" / "transformers" / args.name
    if destination.exists():
        print(f"ERROR: el destino ya existe: {destination}", file=sys.stderr)
        return 2
    try:
        from transformers import AutoModel, AutoTokenizer
    except ImportError as exc:
        print(f"ERROR: falta transformers: {exc}", file=sys.stderr)
        return 2
    try:
        kwargs = {"revision": args.revision} if args.revision else {}
        tokenizer = AutoTokenizer.from_pretrained(args.model, **kwargs)
        model = AutoModel.from_pretrained(args.model, use_safetensors=True, **kwargs)
        destination.mkdir(parents=True, exist_ok=False)
        tokenizer.save_pretrained(str(destination))
        model.save_pretrained(str(destination), safe_serialization=True)
        metadata = {
            "name": args.name,
            "model_type": "transformer",
            "source": args.model,
            "revision": args.revision,
            "framework": "transformers",
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
