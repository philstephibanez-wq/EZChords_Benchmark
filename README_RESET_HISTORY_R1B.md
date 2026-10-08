# EZStudio_lab — RESET HISTORY R1B HOTFIX

R1B corrige le cas observé où `mongosh` n'est pas présent dans le `PATH`.

Ordre MongoDB :

1. utilise `mongosh` s'il est disponible ;
2. sinon utilise `H:\Python\pythoncore-3.14-64\python.exe` + `pymongo` ;
3. vérifie que `ezstudio_lab` n'existe plus.

Le script reste compatible Windows PowerShell 5.1 et accepte `reset`, `RESET`, etc.

Ton exécution R1A a déjà supprimé SQLite et la majorité des dossiers historiques avant l'arrêt. R1B est idempotent : il peut être relancé directement sur cet état partiellement nettoyé.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_RESET_HISTORY_R1B_HOTFIX.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\reset-history-r1.ps1
```

Puis taper `RESET`.

Fin attendue :

```text
EZSTUDIO_MONGO_DROP_PYMONGO_OK
DROPPED MongoDB database ezstudio_lab (pymongo)
EMPTY_DB_SCHEMA_OK
EZSTUDIO_SQLITE_HISTORY_EMPTY_OK
EZSTUDIO_RUNTIME_HISTORY_EMPTY_OK
EZSTUDIO_MONGO_HISTORY_EMPTY_OK
EZSTUDIO_HISTORY_RESET_R1B_OK
```
