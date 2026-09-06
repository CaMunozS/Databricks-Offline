# Model Transport Repository

Repositorio para preparar, validar y transportar modelos de Machine Learning/NLP hacia un Databricks corporativo sin acceso a Internet.

## Principio operativo

**Una carpeta = un modelo autocontenido y transportable.** Cada modelo incluye pesos, configuración, tokenizer, `model-metadata.json` y `validation.ipynb`. La carpeta se puede copiar individualmente al Unity Catalog Volume; no depende de otra carpeta, del cache de Hugging Face ni de Internet.

## Runtime objetivo

El runtime objetivo del repositorio es **Python 3.12.3**.

`pyproject.toml` declara:

```toml
requires-python = ">=3.12.3,<3.13"
```

Además, los scripts de descarga y validación exigen explícitamente Python 3.12.3 para evitar generar evidencia con otra versión.

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
python -m pip install --upgrade pip
pip install -r requirements-staging.txt
```

Antes de preparar un modelo, `python --version` debe mostrar exactamente `Python 3.12.3`.

Linux/macOS:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python --version
python -m pip install --upgrade pip
pip install -r requirements-staging.txt
```

No se modifica automáticamente la instalación global de Python.

## Git LFS y estructura

En el PC corporativo, después de clonar el repositorio, ejecute `git lfs pull` y luego `python scripts/verify_manifest.py`. Confirme que los pesos son archivos reales y no punteros LFS: un puntero es un archivo de texto pequeño, no un modelo utilizable.

Ejecute `git lfs install` si Git LFS está disponible. `.gitattributes` marca pesos grandes (`*.safetensors`, `*.bin`, `*.pt`, `*.pth`, `*.onnx`, `*.gguf`, `*.h5`).

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
```

Use `--revision <commit-o-tag>` para fijar una revisión. Los scripts rechazan destinos existentes, usan carpetas temporales, prefieren `safetensors` y no habilitan `trust_remote_code=True`.

Cada carpeta conserva origen, revisión, framework, licencia y `python_target` en `model-metadata.json`.

## Validación local obligatoria por modelo

Una carpeta de modelo es válida solamente si incluye:

```text
model-metadata.json
validation.ipynb
```

El notebook se ejecuta desde la propia carpeta del modelo y usa únicamente archivos locales. Establece:

```text
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
HF_DATASETS_OFFLINE=1
local_files_only=True
```

El notebook generado registra Python 3.12.3 y verifica en tiempo de ejecución que el kernel realmente utilice Python 3.12.3.

Para volver a ejecutar una evidencia existente:

```powershell
python scripts/validate_notebook.py `
  --path models/embeddings/<nombre-modelo>/validation.ipynb
```

## Manifest y validación

```powershell
python scripts/list_models.py
python scripts/generate_manifest.py
python scripts/verify_manifest.py
```

El manifest se genera con `python_target: 3.12.3` y rechaza modelos cuya metadata corresponda a otro runtime. Un modelo previamente validado con Python 3.11 debe revalidarse en Python 3.12.3 antes de entrar en un nuevo manifest.

## Transferencia a Databricks

Flujo completo:

```text
Python 3.12.3 staging
        ↓
descargar modelo
        ↓
crear metadata
        ↓
generar y ejecutar validation.ipynb offline
        ↓
generar/verificar manifest SHA-256
        ↓
Git / Git LFS
        ↓
PC corporativo: git lfs pull + verify_manifest
        ↓
copiar carpeta individual
        ↓
Databricks Unity Catalog Volume
```

Ejemplo de destino:

```text
/Volumes/<catalog>/<schema>/<volume>/models/embeddings/<modelo>/
```

Los ejemplos bajo `examples/databricks/` consumen solamente rutas `/Volumes/...`, sin fallback a Internet.

## Migración desde Python 3.11

Si una carpeta existente contiene:

```json
"python_target": "3.11"
```

no cambie ese valor manualmente para aparentar compatibilidad.

Debe reejecutarse la validación con Python 3.12.3, regenerar `validation.ipynb`, actualizar la metadata únicamente después de una ejecución correcta y finalmente regenerar el manifest.

## Seguridad

## Databricks Runtime y clonación segura

Para modelos `sentence-transformers` y `transformers` use Databricks Runtime 17.3 ML (`17.3.x-cpu-ml-scala2.13`). El Runtime estándar no incluye las dependencias de NLP y no puede instalarlas desde PyPI. Las librerías son dependencias del runtime, no artefactos que deban viajar en el repositorio.

Después de clonar en Windows, ejecute `git lfs pull` y `python scripts/verify_manifest.py`. Los artefactos bajo `models/` y los archivos JSON se marcan como binarios para impedir conversiones LF/CRLF. Si el verificador informa una conversión CRLF, recupere el archivo indicado con:

```powershell
git -c core.autocrlf=false checkout -- <ruta-del-archivo>
```

En Databricks indique explícitamente `MODEL_PATH=/Volumes/<catalog>/<schema>/<volume>/models/<tipo>/<modelo>` o complete el widget `model_path`. En Runtime 17.3 estándar, seleccione ML Runtime; no intente `pip install` en el cluster. Para `SINGLE_USER`, el principal del cluster requiere `USE CATALOG`, `USE SCHEMA` y `READ VOLUME`.

No incluya credenciales, tokens, secretos, URLs internas, nombres de personas, datos de clientes ni información bancaria. El push nunca se ejecuta automáticamente.
