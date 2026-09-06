# Arquitectura

```text
Hugging Face
      │
      ▼
Staging Python 3.11
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

