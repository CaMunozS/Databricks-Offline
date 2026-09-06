# Transferir a Databricks

Si el repositorio se clonó mediante Git LFS, ejecute antes `git lfs pull` y `python scripts/verify_manifest.py`. No transfiera punteros LFS en lugar de los pesos reales.

La unidad de transferencia es **una carpeta de modelo completa**. No combine archivos de modelos distintos.

Origen de ejemplo:

```text
models/embeddings/paraphrase-multilingual-MiniLM-L12-v2/
```

Destino:

```text
/Volumes/<catalog>/<schema>/<volume>/models/embeddings/paraphrase-multilingual-MiniLM-L12-v2/
```

Copie la carpeta completa mediante el procedimiento manual autorizado. Compruebe que `model-metadata.json`, configuración, tokenizer y pesos quedaron dentro del destino. Luego adapte `<modelo>` en `examples/databricks/load_embedding.py` o `load_transformer.py`.

Los ejemplos establecen `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1` y `local_files_only=True`. No existe fallback hacia Internet. `inspect_volume.py` solo enumera carpetas y no carga pesos.
