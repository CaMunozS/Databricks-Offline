"""Load one local model with Hugging Face offline settings."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--type", choices=("embedding", "transformer"), required=True)
    parser.add_argument("--path", type=Path, required=True)
    args = parser.parse_args()
    path = args.path.resolve()
    if not path.is_dir() or not (path / "model-metadata.json").is_file():
        print("ERROR: la ruta debe ser una carpeta de modelo con model-metadata.json.", file=sys.stderr)
        return 2
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    try:
        if args.type == "embedding":
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(str(path), local_files_only=True)
            result = model.encode(["Texto de validación offline."], normalize_embeddings=True, show_progress_bar=False)
            print(f"Embedding validado: shape={result.shape}")
        else:
            import torch
            from transformers import AutoModel, AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(str(path), local_files_only=True)
            model = AutoModel.from_pretrained(str(path), local_files_only=True)
            tokens = tokenizer("Texto de validación offline.", return_tensors="pt")
            with torch.no_grad():
                outputs = model(**tokens)
            print(f"Transformer validado: last_hidden_state.shape={outputs.last_hidden_state.shape}")
    except Exception as exc:
        print(f"ERROR: la validación offline falló; falta algún archivo local o hay una incompatibilidad: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
