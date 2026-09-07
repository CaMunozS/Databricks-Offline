"""Package an installed spaCy pipeline for offline transport."""
from __future__ import annotations

import argparse
import importlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from notebook_factory import create_validation_notebook
from runtime_config import PYTHON_TARGET
from validate_notebook import execute_notebook


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True, help="Paquete spaCy ya instalado, por ejemplo es_core_news_lg")
    args = parser.parse_args()
    name = args.package
    if Path(name).name != name or name in {".", ".."}:
        print("ERROR: --package debe ser un nombre de paquete simple.", file=sys.stderr)
        return 2
    destination = Path(__file__).resolve().parents[1] / "models" / "spacy" / name
    if destination.exists():
        print(f"ERROR: el destino ya existe: {destination}", file=sys.stderr)
        return 2
    try:
        import spacy

        package = importlib.import_module(name)
        package_root = Path(package.__file__).resolve().parent
        nlp = spacy.load(name)
        package_meta = nlp.meta
        staging = destination.parent / f".{name}.partial-{uuid4().hex}"
        model_version = str(package_meta.get("version", ""))
        model_dirs = sorted(
            path for path in package_root.glob(f"{name}-{model_version}") if path.is_dir()
        )
        if len(model_dirs) != 1:
            raise ValueError(f"No se encontró una única carpeta de datos para {name}.")
        shutil.copytree(model_dirs[0], staging)
        metadata = {
            "name": name,
            "model_type": "spacy",
            "source": f"explosion/spacy-models:{name}",
            "revision": str(package_meta.get("version", "unknown")),
            "framework": "spacy",
            "license": str(package_meta.get("license", "unknown")),
            "task": "nlp-pipeline",
            "language": str(package_meta.get("lang", "unknown")),
            "python_target": PYTHON_TARGET,
            "export_environment": {"python": sys.version.split()[0], "spacy": spacy.__version__},
            "downloaded_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "validation": {"status": "pending"},
        }
        (staging / "model-metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        execute_notebook(create_validation_notebook(staging))
        metadata["validation"] = {"status": "passed"}
        metadata["validation_timestamp_utc"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        (staging / "model-metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        staging.replace(destination)
    except Exception as exc:
        if "staging" in locals() and staging.exists():
            shutil.rmtree(staging)
        print(f"ERROR: no se pudo preparar el pipeline spaCy: {exc}", file=sys.stderr)
        return 1
    print(f"Pipeline spaCy guardado en: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
