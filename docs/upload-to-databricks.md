# Transferir a Databricks

## Verificación obligatoria en el Volume

Después de copiar los modelos, ejecute una verificación desde el entorno autorizado:

```powershell
python scripts/verify_volume.py `
  --volume-root /Volumes/<catalog>/<schema>/<volume>
```

La verificación compara existencia, tamaño y SHA-256 de todos los artefactos contra `model-manifest.json`.

## Runtime y permisos

Los modelos basados en `transformers` o `sentence-transformers` requieren Databricks Runtime 17.3 ML (`17.3.x-cpu-ml-scala2.13`). El Runtime 17.3 estándar no contiene torch, transformers, sentence-transformers, safetensors, tokenizers ni huggingface-hub, y no se debe intentar instalarlos con pip: el entorno no tiene salida a PyPI.

No empaquete esas librerías dentro del repositorio; son dependencias del runtime ML. En clusters `SINGLE_USER`, Unity Catalog evalúa el acceso con el principal asignado al cluster, no con la persona que ejecuta el notebook. Ese principal necesita los grants `USE CATALOG`, `USE SCHEMA` y `READ VOLUME` sobre `<catalog>.<schema>.<volume>`; de lo contrario `/Volumes/...` puede responder `PERMISSION_DENIED` aunque el usuario tenga permisos propios.

`DATABRICKS_RUNTIME_VERSION` no distingue entre Runtime 17.3 estándar y ML: en ambos puede ser `17.3`. El preflight comprueba que estén disponibles `torch`, `transformers` y `sentence-transformers`; si falta alguno, seleccione ML Runtime y no intente instalar desde PyPI.

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
