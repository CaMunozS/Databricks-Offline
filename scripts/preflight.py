"""Preflight diagnostics for local and Databricks offline validation."""
from __future__ import annotations

import importlib.metadata
import os
import sys
from pathlib import Path

from integrity import lfs_pointers


def preflight(model_path: Path) -> None:
    runtime = os.environ.get("DATABRICKS_RUNTIME_VERSION", "local")
    print("PREFLIGHT")
    print(f"Python: {sys.version.split()[0]}")
    print(f"DATABRICKS_RUNTIME_VERSION: {runtime}")
    if runtime != "local" and "17.3" in runtime and "-cpu-ml-" not in runtime:
        raise RuntimeError("Runtime estándar detectado: requiere ML Runtime; no intente pip install porque el cluster no tiene salida a PyPI.")
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
    print("PREFLIGHT OK")
