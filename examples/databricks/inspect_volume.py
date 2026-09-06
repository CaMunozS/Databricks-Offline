"""Inspect model folders in a Unity Catalog Volume without loading models."""
from pathlib import Path

CATALOG = "<catalog>"
SCHEMA = "<schema>"
VOLUME = "<volume>"
VOLUME_ROOT = Path(f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}")
MODELS_ROOT = VOLUME_ROOT / "models"
EMBEDDINGS_ROOT = MODELS_ROOT / "embeddings"
TRANSFORMERS_ROOT = MODELS_ROOT / "transformers"
for label, folder in (("EMBEDDINGS", EMBEDDINGS_ROOT), ("TRANSFORMERS", TRANSFORMERS_ROOT)):
    print(label)
    if folder.exists():
        for model_folder in sorted(folder.iterdir()):
            if model_folder.is_dir():
                print(f"- {model_folder.name}")
    print()
