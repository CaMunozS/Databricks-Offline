# Agregar un modelo

El runtime objetivo para preparar y validar modelos es **Python 3.12.3**.

Ejemplo PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
python scripts/download_embedding.py --model <organizacion/modelo> --name <nombre-modelo> --revision <revision>
python scripts/validate_offline.py --type embedding --path models/embeddings/<nombre-modelo>
python scripts/validate_notebook.py --path models/embeddings/<nombre-modelo>/validation.ipynb
python scripts/generate_manifest.py
python scripts/verify_manifest.py
git add models/embeddings/<nombre-modelo> model-manifest.json
git commit -m "Add embedding model <nombre-modelo>"
```

1. Confirme que `python --version` muestra exactamente Python 3.12.3 y active el entorno de staging.
2. Descargue con `download_embedding.py` o `download_transformer.py`.
3. Revise `model-metadata.json`, licencia, origen, revisión y archivos transportados.
4. Confirme que `python_target` sea `3.12.3`.
5. Ejecute la validación offline y el `validation.ipynb` generado dentro de la carpeta del modelo.
6. Genere el manifest con `generate_manifest.py`.
7. Verifique el manifest con `verify_manifest.py`.
8. Ejecute `git add` sobre la carpeta y el manifest.
9. Ejecute `git commit` con un mensaje descriptivo.
10. Haga `git push` manualmente cuando corresponda; este proyecto nunca hace push automático.

Un modelo que haya sido validado previamente con Python 3.11 debe revalidarse con Python 3.12.3; no cambie la metadata manualmente sin ejecutar nuevamente el notebook.

No habilite `trust_remote_code=True` automáticamente. Un modelo que requiera código remoto debe evaluarse y aprobarse explícitamente.
