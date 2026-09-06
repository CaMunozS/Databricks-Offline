# Model Transport Repository

Repositorio para preparar, validar y transportar modelos de Machine Learning/NLP hacia un Databricks corporativo sin acceso a Internet.

## Principio operativo

**Una carpeta = un modelo autocontenido y transportable.** Cada modelo incluye pesos, configuración, tokenizer y `model-metadata.json`. La carpeta se puede copiar individualmente al Unity Catalog Volume; no depende de otra carpeta, del cache de Hugging Face ni de Internet.

## Requisitos e instalación

El proyecto requiere Python 3.11.x (`>=3.11,<3.12`). Las dependencias de preparación están en `requirements-staging.txt`; esto no implica que se puedan instalar dentro del Databricks corporativo, que usará las librerías aprobadas por su runtime.

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-staging.txt
```

Linux/macOS:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-staging.txt
```

No se modifica automáticamente la instalación global de Python.

## Git LFS y estructura

Ejecute `git lfs install` si Git LFS está disponible. `.gitattributes` marca pesos grandes (`*.safetensors`, `*.bin`, `*.pt`, `*.pth`, `*.onnx`, `*.gguf`, `*.h5`). Si no está instalado, la estructura inicial sigue funcionando, pero los pesos grandes no tendrán manejo LFS.

```text
models/
├── embeddings/<nombre-modelo>/
└── transformers/<nombre-modelo>/
```

No se colocan archivos directamente en las dos carpetas de categoría.

## Descarga en staging

```powershell
python scripts/download_embedding.py `
  --model sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 `
  --name paraphrase-multilingual-MiniLM-L12-v2

python scripts/download_transformer.py `
  --model dccuchile/bert-base-spanish-wwm-cased `
  --name bert-base-spanish-wwm-cased
```

Use `--revision <commit-o-tag>` para fijar una revisión. Los scripts rechazan destinos existentes para evitar sobreescrituras. Usan las funciones oficiales de guardado, prefieren `safetensors` y no habilitan `trust_remote_code=True`.

Cada carpeta conserva el origen, revisión, framework y objetivo Python en `model-metadata.json`. Revise esa metadata y la procedencia antes de incorporar el modelo.

## Manifest y validación

```powershell
python scripts/list_models.py
python scripts/generate_manifest.py
python scripts/verify_manifest.py
python scripts/verify_manifest.py --model-path models/embeddings/paraphrase-multilingual-MiniLM-L12-v2
python scripts/validate_offline.py --type embedding --path models/embeddings/paraphrase-multilingual-MiniLM-L12-v2
python scripts/validate_offline.py --type transformer --path models/transformers/bert-base-spanish-wwm-cased
```

El manifest está organizado por modelo y registra tamaño y SHA-256 por archivo. La validación offline establece `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `local_files_only=True` y falla si faltan archivos locales.

## Transferencia a Databricks

La unidad de transferencia es una carpeta completa, por ejemplo:

```text
models/embeddings/paraphrase-multilingual-MiniLM-L12-v2/
```

que se copia a:

```text
/Volumes/<catalog>/<schema>/<volume>/models/embeddings/paraphrase-multilingual-MiniLM-L12-v2/
```

La carga manual y permisos del Volume siguen el procedimiento corporativo. Los ejemplos bajo `examples/databricks/` consumen solamente rutas `/Volumes/...`, sin fallback a Internet. Consulte `docs/architecture.md`, `docs/add-model.md` y `docs/upload-to-databricks.md`.

## Seguridad

No incluya credenciales, tokens, secretos, URLs internas, nombres de personas, datos de clientes ni información bancaria. El push nunca se ejecuta automáticamente.

