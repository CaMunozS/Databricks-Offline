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

En el PC corporativo, después de clonar el repositorio, ejecute `git lfs pull` y luego `python scripts/verify_manifest.py`. Confirme que los pesos son archivos reales y no punteros LFS: un puntero es un archivo de texto pequeño, no un modelo utilizable.

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

Flujo completo: preparar con Python 3.11, validar offline, generar/verificar manifest, ejecutar `git add` y `git commit`, hacer push manual, clonar o descargar en el PC corporativo, ejecutar `git lfs pull`, validar SHA-256 y transferir una carpeta de modelo completa.

La unidad de transferencia es una carpeta completa, por ejemplo:

```text
models/embeddings/paraphrase-multilingual-MiniLM-L12-v2/
```

que se copia a:

```text
/Volumes/<catalog>/<schema>/<volume>/models/embeddings/paraphrase-multilingual-MiniLM-L12-v2/
```

La carga manual y permisos del Volume siguen el procedimiento corporativo. Los ejemplos bajo `examples/databricks/` consumen solamente rutas `/Volumes/...`, sin fallback a Internet. Consulte `docs/architecture.md`, `docs/add-model.md` y `docs/upload-to-databricks.md`.

## Validación local obligatoria por modelo

Una carpeta de modelo es válida solamente si incluye tanto `model-metadata.json` como `validation.ipynb`. El downloader genera el notebook con `nbformat`, lo ejecuta automáticamente con `nbclient` antes de publicar la carpeta definitiva y conserva las salidas como evidencia técnica. Las rutas locales se redactan antes de guardar el notebook ejecutado.

```text
descargar modelo
        ↓
crear metadata
        ↓
crear validation.ipynb
        ↓
ejecutar notebook localmente y offline
        ↓
validación offline OK
        ↓
generar manifest
        ↓
verificar SHA-256
        ↓
Git / Git LFS
        ↓
PC corporativo: git lfs pull y verificar SHA-256
        ↓
copiar carpeta individual
        ↓
Databricks Volume
```

El notebook se ejecuta con el directorio de trabajo igual a su propia carpeta, carga `MODEL_PATH = Path.cwd()` y establece `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1` y `HF_DATASETS_OFFLINE=1`. Las cargas usan siempre `local_files_only=True`.

Para volver a ejecutar una evidencia existente:

```powershell
python scripts/validate_notebook.py `
  --path models/embeddings/<nombre-modelo>/validation.ipynb
```

Al transportar un modelo, copie también `validation.ipynb`; el manifest registra su SHA-256 junto con metadata, pesos y archivos de configuración.

## Seguridad

No incluya credenciales, tokens, secretos, URLs internas, nombres de personas, datos de clientes ni información bancaria. El push nunca se ejecuta automáticamente.
