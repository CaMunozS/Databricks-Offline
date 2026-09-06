"""Databricks example: load a transformer from a Unity Catalog Volume."""
from pathlib import Path
import os

import torch
from transformers import AutoModel, AutoTokenizer

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
CATALOG = "<catalog>"
SCHEMA = "<schema>"
VOLUME = "<volume>"
VOLUME_ROOT = Path(f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}")
MODELS_ROOT = VOLUME_ROOT / "models"
TRANSFORMERS_ROOT = MODELS_ROOT / "transformers"
model_path = TRANSFORMERS_ROOT / "<modelo>"
if not model_path.exists():
    raise FileNotFoundError(f"No existe el modelo: {model_path}")
tokenizer = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)
model = AutoModel.from_pretrained(str(model_path), local_files_only=True)
tokens = tokenizer("Texto de prueba en español.", return_tensors="pt")
with torch.no_grad():
    outputs = model(**tokens)
print(outputs.last_hidden_state.shape)
