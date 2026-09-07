"""Download and validate a universal Python wheel for offline transport."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from email.parser import Parser
from pathlib import Path
from uuid import uuid4

from notebook_factory import create_validation_notebook
from runtime_config import DATABRICKS_RUNTIME_TARGET, PYTHON_TARGET
from validate_notebook import execute_notebook


def wheel_metadata(wheel: Path) -> dict[str, str]:
    with zipfile.ZipFile(wheel) as archive:
        members = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if len(members) != 1:
            raise ValueError(f"METADATA ambiguo o faltante en {wheel.name}")
        message = Parser().parsestr(archive.read(members[0]).decode("utf-8"))
    return {key: str(message.get(key, "")) for key in ("Name", "Version", "License", "License-Expression")}


def is_universal_wheel(wheel: Path) -> bool:
    return wheel.name.endswith("-py3-none-any.whl") or wheel.name.endswith("-py2.py3-none-any.whl")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True, help="Nombre del paquete en PyPI")
    parser.add_argument("--version", required=True, help="Versi\u00f3n exacta del wheel")
    parser.add_argument("--name", required=True, help="Nombre de la carpeta local")
    parser.add_argument("--import-name", required=True, help="Nombre usado por __import__")
    parser.add_argument("--reason", required=True, help="Motivo de transporte del wheel")
    parser.add_argument("--replace", action="store_true", help="Reemplaza una librer\u00eda existente tras validar")
    args = parser.parse_args()
    if not args.name or Path(args.name).name != args.name or args.name in {".", ".."}:
        print("ERROR: --name debe ser un nombre de carpeta simple.", file=sys.stderr)
        return 2
    destination = Path(__file__).resolve().parents[1] / "models" / "libs" / args.name
    if destination.exists() and not args.replace:
        print(f"ERROR: el destino ya existe: {destination}", file=sys.stderr)
        return 2
    staging = destination.parent / f".{args.name}.partial-{uuid4().hex}"
    try:
        staging.mkdir(parents=True, exist_ok=False)
        subprocess.run(
            [sys.executable, "-m", "pip", "download", f"{args.package}=={args.version}", "--no-deps", "-d", str(staging)],
            check=True,
        )
        wheels = list(staging.glob("*.whl"))
        if len(wheels) != 1:
            raise ValueError(f"Se esperaba exactamente un wheel y se encontraron {len(wheels)}.")
        wheel = wheels[0]
        if not is_universal_wheel(wheel):
            raise ValueError(f"Wheel no universal rechazado: {wheel.name}")
        wheel_info = wheel_metadata(wheel)
        if wheel_info["Name"].lower().replace("_", "-") != args.package.lower().replace("_", "-"):
            raise ValueError(f"El Name del wheel no coincide con --package: {wheel_info['Name']}")
        if wheel_info["Version"] != args.version:
            raise ValueError(f"La versi\u00f3n del wheel no coincide con --version: {wheel_info['Version']}")
        license_name = wheel_info["License-Expression"] or wheel_info["License"] or "unknown"
        metadata = {
            "name": args.name,
            "model_type": "lib",
            "source": f"PyPI:{args.package}",
            "revision": args.version,
            "framework": "pip",
            "license": license_name,
            "python_target": PYTHON_TARGET,
            "wheel_file": wheel.name,
            "import_name": args.import_name,
            "reason": args.reason,
            "install_hint": (
                f"%pip install /Volumes/<catalog>/<schema>/<volume>/models/libs/{args.name}/{wheel.name} "
                "--no-deps --force-reinstall\n"
                "dbutils.library.restartPython()"
            ),
            "databricks_runtime_supported": DATABRICKS_RUNTIME_TARGET,
            "export_environment": {
                "python": sys.version.split()[0],
                "pip": importlib.metadata.version("pip"),
            },
            "downloaded_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "validation": {"status": "pending"},
        }
        metadata_path = staging / "model-metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        execute_notebook(create_validation_notebook(staging))
        metadata["validation"] = {"status": "passed"}
        metadata["validation_timestamp_utc"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
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
        print(f"ERROR: no se pudo preparar la librer\u00eda: {exc}", file=sys.stderr)
        return 1
    print(f"Librer\u00eda guardada en: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
