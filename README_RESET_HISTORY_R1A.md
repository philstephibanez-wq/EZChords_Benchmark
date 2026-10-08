# EZStudio_lab — RESET HISTORY R1A HOTFIX

Correctif PowerShell 5.1 du reset historique.

Le R1 utilisait deux constructions non compatibles avec Windows PowerShell 5.1 :

- `$RuntimeRoot:` dans une chaîne, qui doit être `${RuntimeRoot}:`
- l'opérateur `??`, disponible en PowerShell 7 mais pas en Windows PowerShell 5.1

R1A supprime ces deux incompatibilités.

Aucun changement de périmètre :

Supprimé :
- SQLite historique
- audio historique
- STEMS / observabilité / exports / jobs / uploads / work / launcher / worker
- base MongoDB `ezstudio_lab`

Conservé :
- code / Git
- dépendances Python
- cache Torch
- modèles
- `H:\EZS_orchestrator`

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_RESET_HISTORY_R1A_HOTFIX.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\reset-history-r1.ps1
```

Puis taper :

```text
RESET
```

Sortie finale attendue :

```text
EMPTY_DB_SCHEMA_OK
EZSTUDIO_SQLITE_HISTORY_EMPTY_OK
EZSTUDIO_RUNTIME_HISTORY_EMPTY_OK
EZSTUDIO_MONGO_HISTORY_EMPTY_OK
EZSTUDIO_HISTORY_RESET_R1A_OK
```
