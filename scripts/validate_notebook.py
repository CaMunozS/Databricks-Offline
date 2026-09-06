"""Execute one model validation notebook offline from its own folder."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

import nbformat
from nbclient import NotebookClient

from runtime_config import require_target_python

KERNEL_NAME = "offline-model-validation"


def write_kernel_spec(root: Path) -> None:
    spec_dir = root / "kernels" / KERNEL_NAME
    spec_dir.mkdir(parents=True)
    kernel = {
        "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "Offline model validation",
        "language": "python",
    }
    (spec_dir / "kernel.json").write_text(json.dumps(kernel), encoding="utf-8")


def redact_output(value: object) -> object:
    if not isinstance(value, str):
        return value
    value = re.sub(r"(?m)^Model path:.*$", "Model path: <local model directory>", value)
    value = re.sub(r"(?i)[A-Z]:\\\\Users\\\\[^\\\\\s]+", "<local-user-path>", value)
    value = re.sub(r"(?i)/Users/[^/\s]+", "<local-user-path>", value)
    return value


def sanitize_outputs(notebook: nbformat.NotebookNode) -> None:
    for cell in notebook.cells:
        for output in cell.get("outputs", []):
            if "text" in output:
                output["text"] = redact_output(output["text"])
            if "traceback" in output:
                output["traceback"] = [redact_output(line) for line in output["traceback"]]
            for value in output.get("data", {}).values():
                if isinstance(value, str):
                    output["data"] = {key: redact_output(item) for key, item in output["data"].items()}
                    break


def execute_notebook(notebook_path: Path, timeout: int = 600) -> None:
    require_target_python()
    notebook_path = notebook_path.resolve()
    if notebook_path.name != "validation.ipynb" or not notebook_path.is_file():
        raise ValueError("--path debe apuntar a un validation.ipynb existente.")
    model_dir = notebook_path.parent
    if not (model_dir / "model-metadata.json").is_file():
        raise ValueError("La carpeta del notebook no contiene model-metadata.json.")
    notebook = nbformat.read(notebook_path, as_version=4)
    notebook.metadata.setdefault("kernelspec", {})["name"] = KERNEL_NAME
    with tempfile.TemporaryDirectory(prefix="offline-model-kernel-") as temporary_dir:
        kernel_root = Path(temporary_dir)
        write_kernel_spec(kernel_root)
        previous_jupyter_path = os.environ.get("JUPYTER_PATH")
        os.environ["JUPYTER_PATH"] = str(kernel_root) + (os.pathsep + previous_jupyter_path if previous_jupyter_path else "")
        try:
            client = NotebookClient(notebook, timeout=timeout, kernel_name=KERNEL_NAME)
            client.execute(cwd=str(model_dir))
        finally:
            if previous_jupyter_path is None:
                os.environ.pop("JUPYTER_PATH", None)
            else:
                os.environ["JUPYTER_PATH"] = previous_jupyter_path
    sanitize_outputs(notebook)
    nbformat.write(notebook, notebook_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, required=True, help="Ruta a validation.ipynb")
    parser.add_argument("--timeout", type=int, default=600, help="Máximo de segundos por celda")
    args = parser.parse_args()
    try:
        execute_notebook(args.path, timeout=args.timeout)
    except Exception as exc:
        print(f"ERROR: el notebook de validación falló: {exc}", file=sys.stderr)
        return 1
    print(f"VALIDATION NOTEBOOK OK: {args.path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
