# EZStudio — TERMINOLOGY PRESET R2A

R2A aligne **persistance + UI** avec la terminologie canonique :

`Chaîne → Phase → Module → Engine/Model → Settings → Preset → Adapter`

Aucun algorithme scientifique n'est modifié.

## Sécurité de migration

La migration SQLite :
1. refuse de démarrer si un job est `queued`, `running` ou `cancelling`;
2. crée automatiquement une sauvegarde cohérente de `data/benchmark.sqlite`;
3. migre tables, colonnes et valeurs;
4. vérifie les nombres de lignes avant/après;
5. exécute `PRAGMA foreign_key_check`;
6. exécute `PRAGMA integrity_check`.

La sauvegarde est affichée dans la console sous la forme :

`benchmark.sqlite.pre-20261010_preset_terminology_r2a-....bak`

## Application

Arrêter d'abord serveur/worker afin qu'aucun job ne puisse démarrer pendant la migration.

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_TERMINOLOGY_PRESET_R2A.zip" -C H:\EZStudio_lab

powershell -ExecutionPolicy Bypass -File .\scripts\apply_terminology_preset_r2a.ps1

php bin\console lint:container
php bin\console lint:twig templates
php bin\console cache:clear

H:\Python\pythoncore-3.14-64\python.exe .\scripts\test_profile_r3b35c_contract.py
H:\Python\pythoncore-3.14-64\python.exe .\scripts\test_declarative_runtime_v1b.py

git diff --check
git status --short
```

Résultats attendus :

```text
TERMINOLOGY_PRESET_R2A_DB_MIGRATION_OK
TERMINOLOGY_PRESET_R2A_CODE_APPLIED
TERMINOLOGY_PRESET_R2A_CONTRACT_OK
TERMINOLOGY_GREP_R2A_OK
TERMINOLOGY_PRESET_R2A_APPLIED
```

Le grep résiduel est écrit dans :

`TERMINOLOGY_GREP_R2A_AFTER.txt`

## Important

R2A ne renomme pas encore les internals Python PROFILE `gene.py / gene_registry.py / genes/* / gene_spec.py`.
Ce sera R2B, uniquement après validation fonctionnelle de R2A.
