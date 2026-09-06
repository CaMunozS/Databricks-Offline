"""Inspect model folders in a Unity Catalog Volume without loading models."""
from pathlib import Path

CATALOG = "<catalog>"
SCHEMA = "<schema>"
VOLUME = "<volume>"
VOLUME_ROOT = Path(f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}")
MODELS_ROOT = VOLUME_ROOT / "models"
for label, folder_name in (("EMBEDDINGS", "embeddings"), ("TRANSFORMERS", "transformers")):
    print(label)
    folder = MODELS_ROOT / folder_name
    if folder.exists():
        for model_folder in sorted(folder.iterdir()):
            if model_folder.is_dir():
                print(model_folder.name)
    print()
