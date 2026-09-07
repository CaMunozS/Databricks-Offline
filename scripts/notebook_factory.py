"""Create a self-contained offline validation notebook for one model folder."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

KERNEL_NAME = "offline-model-validation"
REQUIRED_METADATA = ("name", "model_type", "source", "revision", "framework", "python_target", "downloaded_at_utc")


def read_metadata(model_dir: Path) -> dict[str, object]:
    metadata_path = model_dir / "model-metadata.json"
    if not metadata_path.is_file():
        raise ValueError(f"Falta metadata: {metadata_path}")
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Metadata JSON inválida: {metadata_path}: {exc}") from exc
    missing = [field for field in REQUIRED_METADATA if field not in metadata]
    if missing:
        raise ValueError(f"Metadata incompleta: faltan {', '.join(missing)}")
    # La descarga se prepara en una carpeta .partial y se renombra sólo tras
    # ejecutar la validación; la coincidencia definitiva la exige el manifest.
    if not model_dir.name.startswith(".") and metadata["name"] != model_dir.name:
        raise ValueError("El nombre de metadata no coincide con la carpeta del modelo.")
    if metadata["model_type"] not in {"embedding", "transformer"}:
        raise ValueError("model_type debe ser embedding o transformer.")
    return metadata


def base_cells(expected_type: str, model_name: str) -> list[object]:
    return [
        new_markdown_cell(
            "# Validación offline del modelo\n\n"
            "Este notebook se ejecuta desde la carpeta del modelo y no usa Internet."
        ),
        new_code_cell(
            "import os\n\n"
            "os.environ['HF_HUB_OFFLINE'] = '1'\n"
            "os.environ['TRANSFORMERS_OFFLINE'] = '1'\n"
            "os.environ['HF_DATASETS_OFFLINE'] = '1'"
        ),
        new_code_cell(
            "from pathlib import Path\n"
            "import json\n"
            "import os\n"
            "import sys\n"
            "import platform\n"
            "import importlib.metadata\n\n"
            "def resolve_model_path():\n"
            "    configured = os.environ.get('MODEL_PATH', '').strip()\n"
            "    if configured:\n"
            "        return Path(configured).expanduser().resolve()\n"
            "    if os.environ.get('DATABRICKS_RUNTIME_VERSION'):\n"
            "        try:\n"
            "            dbutils.widgets.text('model_path', '')\n"
            "            configured = dbutils.widgets.get('model_path').strip()\n"
            "        except Exception:\n"
            "            configured = ''\n"
            "        if configured:\n"
            "            return Path(configured).resolve()\n"
            "        raise RuntimeError('En Databricks indique MODEL_PATH o el widget model_path con una ruta /Volumes/...')\n"
            "    working_directory = Path.cwd().resolve()\n"
            "    if (working_directory / 'model-metadata.json').is_file():\n"
            "        return working_directory\n"
            f"    relative_model = Path('models') / '{expected_type}s' / '{model_name}'\n"
            "    for root in (working_directory, *working_directory.parents):\n"
            "        candidate = root / relative_model\n"
            "        if (candidate / 'model-metadata.json').is_file():\n"
            "            return candidate.resolve()\n"
            "    raise RuntimeError(\n"
            "        'No se encontró la carpeta del modelo. Ejecute desde el repositorio o defina MODEL_PATH.'\n"
            "    )\n\n"
            "MODEL_PATH = resolve_model_path()\n"
            "runtime = os.environ.get('DATABRICKS_RUNTIME_VERSION', 'local')\n"
            "print('PREFLIGHT')\n"
            "print(f'Python: {sys.version.split()[0]}')\n"
            "print(f'DATABRICKS_RUNTIME_VERSION: {runtime}')\n"
            "# DATABRICKS_RUNTIME_VERSION no distingue Runtime estándar de ML.\n"
            "# Se valida la capacidad requerida comprobando los paquetes instalados.\n"
            "for package in ('torch', 'transformers', 'sentence-transformers'):\n"
            "    try:\n"
            "        print(f'{package}: {importlib.metadata.version(package)}')\n"
            "    except importlib.metadata.PackageNotFoundError as exc:\n"
            "        raise RuntimeError(f'Falta {package}; use ML Runtime. No se puede instalar desde PyPI.') from exc\n"
            "try:\n"
            "    assert MODEL_PATH.is_dir(), f'No existe MODEL_PATH: {MODEL_PATH}'\n"
            "    next(MODEL_PATH.iterdir(), None)\n"
            "except PermissionError as exc:\n"
            "    raise RuntimeError('Sin acceso al Volume. En SINGLE_USER se requieren USE CATALOG, USE SCHEMA y READ VOLUME para el principal del cluster.') from exc\n"
            "LFS_PREFIX = b'version https://git-lfs.github.com/spec/v1'\n"
            "for artifact in MODEL_PATH.rglob('*'):\n"
            "    if artifact.is_file():\n"
            "        with artifact.open('rb') as handle:\n"
            "            if handle.read(len(LFS_PREFIX)).startswith(LFS_PREFIX):\n"
            "                raise RuntimeError(f'Puntero Git LFS detectado: {artifact.name}. Ejecute git lfs pull.')\n"
            "print('PREFLIGHT OK')\n"
            "metadata_path = MODEL_PATH / 'model-metadata.json'\n"
            "metadata = json.loads(metadata_path.read_text(encoding='utf-8'))\n"
            "required_fields = {'name', 'model_type', 'source', 'revision', 'framework', 'python_target'}\n"
            "missing_fields = required_fields - metadata.keys()\n"
            "assert not missing_fields, f'Metadata incompleta: {sorted(missing_fields)}'\n"
            "assert MODEL_PATH.name.startswith('.') or metadata['name'] == MODEL_PATH.name, 'El nombre no coincide con la carpeta'\n"
            f"assert metadata['model_type'] == '{expected_type}', 'Tipo de modelo incorrecto'\n"
            "from packaging.specifiers import SpecifierSet\n"
            "from packaging.version import Version\n"
            "python_target = metadata['python_target']\n"
            "if Version(platform.python_version()) not in SpecifierSet(python_target):\n"
            "    print(f'ADVERTENCIA: Python {platform.python_version()} queda fuera de python_target {python_target}; la evidencia no prueba compatibilidad.')\n"
            "print(f'Model path: {MODEL_PATH.resolve()}')\n"
            "for field in ('name', 'model_type', 'source', 'revision', 'framework', 'python_target', 'export_environment'):\n"
            "    print(f'{field}: {metadata[field]}')\n"
            "print('Versiones que producen esta evidencia:')\n"
            "for package in ('sentence-transformers', 'transformers', 'torch'):\n"
            "    print(f'{package}: {importlib.metadata.version(package)}')\n"
            "print(f'Python: {platform.python_version()}')"
        ),
    ]


def embedding_cells() -> list[object]:
    return [
        new_code_cell(
            "from sentence_transformers import SentenceTransformer\n\n"
            "model = SentenceTransformer(\n"
            "    str(MODEL_PATH),\n"
            "    local_files_only=True,\n"
            "    trust_remote_code=False,\n"
            ")"
        ),
        new_code_cell(
            "import numpy as np\n\n"
            "texts = [\n"
            "    'Cliente solicita financiamiento para capital de trabajo.',\n"
            "    'La empresa presenta crecimiento sostenido de ventas.',\n"
            "    'La compañía mantiene una posición financiera estable.',\n"
            "]\n"
            "embeddings = model.encode(\n"
            "    texts,\n"
            "    normalize_embeddings=True,\n"
            "    show_progress_bar=False,\n"
            ")\n"
            "assert embeddings.shape[0] == len(texts)\n"
            "assert embeddings.ndim == 2\n"
            "assert embeddings.shape[1] > 0\n"
            "assert np.isfinite(embeddings).all()\n"
            "print(f'modelo: {metadata[\"name\"]}')\n"
            "print(f'cantidad de textos: {len(texts)}')\n"
            "print(f'shape: {embeddings.shape}')\n"
            "print(f'dimensión del embedding: {embeddings.shape[1]}')\n"
            "print(f'dtype: {embeddings.dtype}')\n"
            "print('resultado: OK')"
        ),
    ]


def transformer_cells() -> list[object]:
    return [
        new_code_cell(
            "import torch\n"
            "from transformers import AutoModel, AutoTokenizer\n\n"
            "tokenizer = AutoTokenizer.from_pretrained(\n"
            "    str(MODEL_PATH),\n"
            "    local_files_only=True,\n"
            "    trust_remote_code=False,\n"
            ")\n"
            "model = AutoModel.from_pretrained(\n"
            "    str(MODEL_PATH),\n"
            "    local_files_only=True,\n"
            "    trust_remote_code=False,\n"
            ")"
        ),
        new_code_cell(
            "text = 'La empresa presenta crecimiento sostenido de sus ingresos.'\n"
            "inputs = tokenizer(text, return_tensors='pt', truncation=True)\n"
            "with torch.no_grad():\n"
            "    outputs = model(**inputs)\n"
            "assert outputs.last_hidden_state is not None\n"
            "assert outputs.last_hidden_state.ndim == 3\n"
            "assert outputs.last_hidden_state.shape[0] == 1\n"
            "assert torch.isfinite(outputs.last_hidden_state).all()\n"
            "print(f'modelo: {metadata[\"name\"]}')\n"
            "print(f'input shape: {inputs[\"input_ids\"].shape}')\n"
            "print(f'last_hidden_state shape: {outputs.last_hidden_state.shape}')\n"
            "print(f'dtype: {outputs.last_hidden_state.dtype}')\n"
            "print('resultado: OK')"
        ),
    ]


def create_validation_notebook(model_dir: Path) -> Path:
    model_dir = model_dir.resolve()
    metadata = read_metadata(model_dir)
    model_type = str(metadata["model_type"])
    cells = base_cells(model_type, model_dir.name)
    cells.extend(embedding_cells() if model_type == "embedding" else transformer_cells())
    cells.append(new_code_cell("print('VALIDATION OK')\nprint('Modelo cargado y ejecutado usando únicamente archivos locales.')"))
    notebook = new_notebook(
        cells=cells,
        metadata={
            "kernelspec": {"display_name": "Offline model validation", "language": "python", "name": KERNEL_NAME},
            "language_info": {"name": "python", "version": "3.12"},
        },
    )
    output_path = model_dir / "validation.ipynb"
    nbformat.write(notebook, output_path)
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        path = create_validation_notebook(args.model_dir)
    except (OSError, ValueError) as exc:
        print(f"ERROR: no se pudo crear el notebook: {exc}")
        return 1
    print(f"Notebook de validación creado: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
