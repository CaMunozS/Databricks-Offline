"""Download one Sentence Transformers model into a self-contained folder."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from model_registry import review_model
from notebook_factory import create_validation_notebook
from runtime_config import PYTHON_TARGET, current_runtime, require_target_python
from validate_notebook import execute_notebook


def main() -> int:
    try:
        require_target_python()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Hugging Face model identifier")
    parser.add_argument("--name", required=True, help="Local folder name")
    parser.add_argument("--revision", default=None, help="Optional Hugging Face revision")
    parser.add_argument("--replace", action="store_true", help="Reexporta y reemplaza una carpeta existente tras validar.")
    args = parser.parse_args()
    if not args.name or Path(args.name).name != args.name or args.name in {".", ".."}:
        print("ERROR: --name debe ser un nombre de carpeta simple.", file=sys.stderr)
        return 2
    destination = Path(__file__).resolve().parents[1] / "models" / "embeddings" / args.name
    if destination.exists() and not args.replace:
        print(f"ERROR: el destino ya existe: {destination}", file=sys.stderr)
        return 2
    staging = destination.parent / f".{args.name}.partial-{uuid4().hex}"
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        print(f"ERROR: falta sentence-transformers: {exc}", file=sys.stderr)
        return 2
    try:
        reviewed = review_model(args.model, args.revision)
        load_options = {"revision": reviewed.revision}
        model = SentenceTransformer(args.model, trust_remote_code=False, **load_options)
        staging.mkdir(parents=True, exist_ok=False)
        model.save(str(staging), safe_serialization=True)
        metadata = {
            "name": args.name,
            "model_type": "embedding",
            "source": args.model,
            "revision": reviewed.revision,
            "framework": "sentence-transformers",
            "license": reviewed.license,
            "python_target": PYTHON_TARGET,
            "databricks_runtime_supported": "17.3 ML Runtime (Python 3.12.3)",
            "export_environment": current_runtime(),
            "downloaded_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "validation": {"status": "pending"},
        }
        (staging / "model-metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        validation_notebook = create_validation_notebook(staging)
        execute_notebook(validation_notebook)
        metadata["validation"] = {"status": "passed"}
        metadata["validation_timestamp_utc"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        (staging / "model-metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if destination.exists():
            backup = destination.parent / f".{args.name}.backup-{uuid4().hex}"
            destination.replace(backup)
            try:
                staging.replace(destination)
            except Exception:
                backup.replace(destination)
                raise
            shutil.rmtree(backup)
        else:
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
