"""Verify model files against model-manifest.json."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", type=Path, help="Optional single model folder")
    args = parser.parse_args()
    manifest_path = ROOT / "model-manifest.json"
    if not manifest_path.exists():
        print(f"ERROR: no existe {manifest_path}", file=sys.stderr)
        return 2
    entries = json.loads(manifest_path.read_text(encoding="utf-8")).get("models", [])
    selected = args.model_path.resolve() if args.model_path else None
    failures: list[str] = []
    matched = 0
    for model in entries:
        folder = (ROOT / model["relative_path"]).resolve()
        if selected and folder != selected:
            continue
        matched += 1
        expected = {item["path"]: item for item in model.get("files", [])}
        actual = {path.relative_to(folder).as_posix(): path for path in folder.rglob("*") if path.is_file()} if folder.exists() else {}
        for relative, item in expected.items():
            path = folder / relative
            if not path.exists():
                failures.append(f"faltante: {path}")
            elif path.stat().st_size != item["bytes"]:
                failures.append(f"tamaño incorrecto: {path}")
            elif digest(path) != item["sha256"]:
                failures.append(f"SHA-256 incorrecto: {path}")
        for relative in sorted(set(actual) - set(expected)):
            failures.append(f"archivo adicional: {folder / relative}")
    if selected and matched == 0:
        failures.append(f"modelo no encontrado en el manifest: {selected}")
    if failures:
        print("Manifest inválido:")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1
    print(f"Manifest correcto: {matched} modelo(s) verificado(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
