"""Preflight diagnostics for local and Databricks offline validation."""
from __future__ import annotations

import importlib.metadata
import os
import sys
from pathlib import Path

from integrity import lfs_pointers
from runtime_config import python_minor_warning


def preflight(model_path: Path) -> None:
    runtime = os.environ.get("DATABRICKS_RUNTIME_VERSION", "local")
    print("PREFLIGHT")
    print(f"Python: {sys.version.split()[0]}")
    print(f"DATABRICKS_RUNTIME_VERSION: {runtime}")
    # DATABRICKS_RUNTIME_VERSION vale simplemente "17.3" tanto para Runtime
    # estándar como ML. La capacidad real se comprueba con los paquetes abajo.
    for package in ("torch", "transformers", "sentence-transformers"):
        try:
            print(f"{package}: {importlib.metadata.version(package)}")
        except importlib.metadata.PackageNotFoundError as exc:
            raise RuntimeError(f"Falta {package}; se requiere ML Runtime y no se puede instalar desde PyPI.") from exc
    try:
        if not model_path.is_dir():
            raise FileNotFoundError(model_path)
        next(model_path.iterdir(), None)
    except PermissionError as exc:
        raise RuntimeError("Sin acceso al Volume. En SINGLE_USER se requieren USE CATALOG, USE SCHEMA y READ VOLUME para el principal del cluster.") from exc
    pointers = lfs_pointers(model_path)
    if pointers:
        raise RuntimeError(f"Puntero Git LFS detectado: {pointers[0]}. Ejecute git lfs pull.")
    import json
    try:
        metadata = json.loads((model_path / "model-metadata.json").read_text(encoding="utf-8"))
        warning = python_minor_warning(metadata.get("python_target"))
        if warning:
            print(warning)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"model-metadata.json inválido: {exc}") from exc
    print("PREFLIGHT OK")
