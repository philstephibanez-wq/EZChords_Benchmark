# EZStudio_lab — RESET HISTORY R1C HOTFIX

R1C corrige le bootstrap PHP de R1B.

Erreur R1B observée :

```text
require(H:\EZStudio_lab\var/vendor/autoload.php)
```

Le fichier temporaire vit dans `var/`, donc `__DIR__` ne peut pas servir de
racine projet. R1C injecte explicitement la racine `H:\EZStudio_lab`.

R1C écrit aussi ses fichiers temporaires en UTF-8 sans BOM.

Le reset est idempotent. L'état déjà partiellement nettoyé peut être repris
directement.

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_RESET_HISTORY_R1C_HOTFIX.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\reset-history-r1.ps1
```

Tape `RESET`.

Fin attendue :

```text
EMPTY_DB_SCHEMA_OK
EZSTUDIO_SQLITE_HISTORY_EMPTY_OK
EZSTUDIO_RUNTIME_HISTORY_EMPTY_OK
EZSTUDIO_MONGO_HISTORY_EMPTY_OK
EZSTUDIO_HISTORY_RESET_R1C_OK
```
