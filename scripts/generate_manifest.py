"""Generate a per-model SHA-256 manifest."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from runtime_config import DATABRICKS_RUNTIME_TARGET, PYTHON_TARGET

ROOT = Path(__file__).resolve().parents[1]
MODEL_TYPES = (("embeddings", "embedding", "sentence-transformers"), ("transformers", "transformer", "transformers"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_metadata(path: Path, folder_name: str, expected_type: str, expected_framework: str) -> dict[str, object]:
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"metadata inválida en {path}: {exc}") from exc
    required = ("name", "model_type", "source", "revision", "framework", "license", "python_target", "downloaded_at_utc", "validation")
    missing = [key for key in required if key not in metadata]
    if missing:
        raise ValueError(f"metadata incompleta en {path}: falta {', '.join(missing)}")
    if metadata["model_type"] != expected_type or metadata["framework"] != expected_framework:
        raise ValueError(f"metadata inconsistente en {path}")
    if metadata["name"] != folder_name:
        raise ValueError(f"el nombre en metadata no coincide con la carpeta: {path}")
    if metadata["validation"].get("status") not in {"passed", "passed_with_version_warning"}:
        raise ValueError(f"modelo sin validación aprobada: {path}")
    return metadata


def main() -> int:
    models: list[dict[str, object]] = []
    try:
        for folder_type, model_type, framework in MODEL_TYPES:
            base = ROOT / "models" / folder_type
            invalid_files = [path for path in base.iterdir() if path.is_file() and path.name != ".gitkeep"] if base.exists() else []
            if invalid_files:
                raise ValueError(f"archivo no permitido en {base}: {invalid_files[0].name}")
            folders = sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith(".")) if base.exists() else []
            for folder in folders:
                metadata_path = folder / "model-metadata.json"
                if not metadata_path.is_file():
                    raise ValueError(f"modelo incompleto: falta {metadata_path}")
                validation_path = folder / "validation.ipynb"
                if not validation_path.is_file():
                    raise ValueError(f"modelo incompleto: falta {validation_path}")
                metadata = read_metadata(metadata_path, folder.name, model_type, framework)
                files = []
                paths = sorted((p for p in folder.rglob("*") if p.is_file()), key=lambda item: item.relative_to(folder).as_posix())
                for path in paths:
                    files.append({"path": path.relative_to(folder).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)})
                models.append({"name": metadata["name"], "type": model_type, "relative_path": folder.relative_to(ROOT).as_posix(), "files": files})
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    payload = {"generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "python_target": PYTHON_TARGET, "databricks_runtime_target": DATABRICKS_RUNTIME_TARGET, "models": models}
    target = ROOT / "model-manifest.json"
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Manifest generado: {target} ({len(models)} modelos)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
