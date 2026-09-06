# Agregar un modelo

Ejemplo PowerShell:

```powershell
python scripts/download_embedding.py --model <organizacion/modelo> --name <nombre-modelo> --revision <revision>
python scripts/validate_offline.py --type embedding --path models/embeddings/<nombre-modelo>
python scripts/generate_manifest.py
python scripts/verify_manifest.py
git add models/embeddings/<nombre-modelo> model-manifest.json
git commit -m "Add embedding model <nombre-modelo>"
```

1. Confirme que Python es 3.11.x y active el entorno de staging.
2. Descargue con `download_embedding.py` o `download_transformer.py`.
3. Revise `model-metadata.json`, licencia, origen, revisión y archivos transportados.
4. Valide offline con `validate_offline.py`.
5. Genere el manifest con `generate_manifest.py`.
6. Verifique el manifest con `verify_manifest.py`.
7. Ejecute `git add` sobre la carpeta y el manifest.
8. Ejecute `git commit` con un mensaje descriptivo.
9. Haga `git push` manualmente cuando corresponda; este proyecto nunca hace push automático.

No habilite `trust_remote_code=True` automáticamente. Un modelo que requiera código remoto debe evaluarse y aprobarse explícitamente.
