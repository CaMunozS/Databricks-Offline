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
    if metadata["name"] != model_dir.name:
        raise ValueError("El nombre de metadata no coincide con la carpeta del modelo.")
    if metadata["model_type"] not in {"embedding", "transformer"}:
        raise ValueError("model_type debe ser embedding o transformer.")
    return metadata


def base_cells(expected_type: str) -> list[object]:
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
            "import json\n\n"
            "MODEL_PATH = Path.cwd().resolve()\n"
            "metadata_path = MODEL_PATH / 'model-metadata.json'\n"
            "metadata = json.loads(metadata_path.read_text(encoding='utf-8'))\n"
            "required_fields = {'name', 'model_type', 'source', 'revision', 'framework', 'python_target'}\n"
            "missing_fields = required_fields - metadata.keys()\n"
            "assert not missing_fields, f'Metadata incompleta: {sorted(missing_fields)}'\n"
            "assert metadata['name'] == MODEL_PATH.name, 'El nombre no coincide con la carpeta'\n"
            f"assert metadata['model_type'] == '{expected_type}', 'Tipo de modelo incorrecto'\n"
            "print(f'Model path: {MODEL_PATH.resolve()}')\n"
            "for field in ('name', 'model_type', 'source', 'revision', 'framework', 'python_target'):\n"
            "    print(f'{field}: {metadata[field]}')"
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
    cells = base_cells(model_type)
    cells.extend(embedding_cells() if model_type == "embedding" else transformer_cells())
    cells.append(new_code_cell("print('VALIDATION OK')\nprint('Modelo cargado y ejecutado correctamente en modo offline.')"))
    notebook = new_notebook(
        cells=cells,
        metadata={
            "kernelspec": {"display_name": "Offline model validation", "language": "python", "name": KERNEL_NAME},
            "language_info": {"name": "python", "version": "3.11"},
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
