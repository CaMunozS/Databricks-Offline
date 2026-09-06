"""Databricks example: load an embedding model from a Unity Catalog Volume."""
from pathlib import Path
import os

from sentence_transformers import SentenceTransformer

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
CATALOG = "<catalog>"
SCHEMA = "<schema>"
VOLUME = "<volume>"
VOLUME_ROOT = Path(f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}")
MODELS_ROOT = VOLUME_ROOT / "models"
EMBEDDINGS_ROOT = MODELS_ROOT / "embeddings"
model_path = EMBEDDINGS_ROOT / "<modelo>"
if not model_path.exists():
    raise FileNotFoundError(f"No existe el modelo: {model_path}")
model = SentenceTransformer(str(model_path), local_files_only=True)
texts = ["Cliente solicita financiamiento para capital de trabajo.", "La empresa presenta crecimiento sostenido de ventas."]
embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
print(f"cantidad de textos: {len(texts)}")
print(f"shape: {embeddings.shape}")
print(f"dimensión del embedding: {embeddings.shape[1]}")
