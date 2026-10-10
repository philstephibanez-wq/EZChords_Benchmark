# R2A — scoped terminology grep fix

Le premier grep R2A utilisait `Path.rglob()` sur tout le répertoire local et pouvait inclure des environnements/dépendances non suivis, ce qui explique le chiffre artificiel de 6661 occurrences.

Ce correctif utilise :

`git ls-files -co --exclude-standard`

puis limite l'analyse à :

- `src/`
- `templates/`
- `python/`
- `scripts/`
- `tests/`
- `config/`
- `contracts/`
- `presets/`
- `adn/`

Les répertoires `vendor`, `var`, `data`, `.venv`, `node_modules`, etc. sont exclus.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_TERMINOLOGY_R2A_GREP_FIX.zip" -C H:\EZStudio_lab

powershell -ExecutionPolicy Bypass -File .\scripts\apply_terminology_r2a_grep_fix.ps1
```

Le rapport corrigé écrase :

`TERMINOLOGY_GREP_R2A_AFTER.txt`
