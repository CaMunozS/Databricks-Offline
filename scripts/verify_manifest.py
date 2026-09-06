"""Verify model files against model-manifest.json."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from integrity import is_lfs_pointer, looks_like_crlf_conversion

ROOT = Path(__file__).resolve().parents[1]
MODEL_FOLDERS = ("embeddings", "transformers")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def discovered_model_paths() -> set[str]:
    paths: set[str] = set()
    for model_type in MODEL_FOLDERS:
        base = ROOT / "models" / model_type
        if not base.exists():
            continue
        for folder in base.iterdir():
            if folder.is_dir() and not folder.name.startswith("."):
                paths.add(folder.relative_to(ROOT).as_posix())
    return paths


def unexpected_category_files() -> list[Path]:
    invalid: list[Path] = []
    for model_type in MODEL_FOLDERS:
        base = ROOT / "models" / model_type
        if base.exists():
            invalid.extend(path for path in base.iterdir() if path.is_file() and path.name != ".gitkeep")
    return invalid


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", type=Path, help="Optional single model folder")
    args = parser.parse_args()
    manifest_path = ROOT / "model-manifest.json"
    if not manifest_path.exists():
        print(f"ERROR: no existe {manifest_path}", file=sys.stderr)
        return 2
    try:
        entries = json.loads(manifest_path.read_text(encoding="utf-8")).get("models", [])
    except json.JSONDecodeError as exc:
        print(f"ERROR: manifest JSON inválido: {exc}", file=sys.stderr)
        return 2
    if not isinstance(entries, list):
        print("ERROR: models debe ser una lista en el manifest.", file=sys.stderr)
        return 2
    selected = args.model_path.resolve() if args.model_path else None
    failures: list[str] = []
    matched = 0
    manifest_paths = {model.get("relative_path") for model in entries if isinstance(model, dict)}
    if not selected:
        for path in unexpected_category_files():
            failures.append(f"archivo no permitido en carpeta de categoría: {path}")
        for relative in sorted(discovered_model_paths() - manifest_paths):
            failures.append(f"modelo no incluido en el manifest: {ROOT / relative}")
    for model in entries:
        if not isinstance(model, dict) or not isinstance(model.get("relative_path"), str):
            failures.append("entrada inválida en el manifest")
            continue
        folder = (ROOT / model["relative_path"]).resolve()
        if selected and folder != selected:
            continue
        matched += 1
        expected = {item["path"]: item for item in model.get("files", []) if isinstance(item, dict) and isinstance(item.get("path"), str)}
        actual = {path.relative_to(folder).as_posix(): path for path in folder.rglob("*") if path.is_file()} if folder.exists() else {}
        if not folder.is_dir():
            failures.append(f"carpeta de modelo faltante: {folder}")
        elif not (folder / "validation.ipynb").is_file():
            failures.append(f"notebook de validación faltante: {folder / 'validation.ipynb'}")
        for relative, item in expected.items():
            path = folder / relative
            if not path.exists():
                failures.append(f"faltante: {path}")
            elif is_lfs_pointer(path):
                failures.append(f"puntero Git LFS: {path}. Ejecute git lfs pull.")
            elif path.stat().st_size != item.get("bytes"):
                if looks_like_crlf_conversion(path, item.get("bytes", 0)):
                    failures.append(
                        f"tamaño incorrecto compatible con conversión CRLF: {path}. "
                        f"Recupere con: git -c core.autocrlf=false checkout -- {path}"
                    )
                else:
                    failures.append(f"tamaño incorrecto: {path}")
            elif digest(path) != item.get("sha256"):
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
