# Arquitectura

```text
Hugging Face
      │
      ▼
Staging Python 3.12.3
      │
      ▼
models/
├── embeddings/
└── transformers/
      │
      ▼
Git / Git LFS
      │
      ▼
PC corporativo
      │
      ▼
copia de carpeta individual
      │
      ▼
Unity Catalog Volume
      │
      ▼
Databricks
```

Cada carpeta bajo `models/embeddings/` o `models/transformers/` es una unidad autónoma. La ejecución en Databricks establece modo offline, usa `local_files_only=True` y carga desde `/Volumes/<catalog>/<schema>/<volume>/models/...`.

La preparación y validación local del artefacto se realiza con Python 3.12.3. Los modelos previamente validados con otro runtime deben revalidarse antes de regenerar el manifest del repositorio.
