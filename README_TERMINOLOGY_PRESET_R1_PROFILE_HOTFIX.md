# EZStudio — TERMINOLOGY PRESET R1 PROFILE HOTFIX

## Cause

Le renommage R1 avait transformé l'injection :

```php
DnaRegistry $dna
```

en :

```php
AnalysisRunRegistry $runs
```

Dans `ProfileController::index()`, `$runs` est déjà le tableau local des runs PROFILE.

Le renommage créait donc une collision de variable et provoquait :

```text
Call to a member function runsForSongItem() on array
```

## Correction

Le nom canonique du service devient :

```php
AnalysisRunRegistry $runRegistry
```

Les tableaux de résultats restent `$runs`.

Le script R1 original est également durci pour ne pas recréer cette collision lors d'une réapplication.

Aucune logique scientifique, persistence, configuration ou algorithme n'est modifié.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_TERMINOLOGY_PRESET_R1_PROFILE_HOTFIX.zip" -C H:\EZStudio_lab

powershell -ExecutionPolicy Bypass -File .\scripts\apply_terminology_preset_r1_profile_hotfix.ps1

php .\scripts\test_terminology_preset_r1_profile_hotfix.php

php bin\console lint:container
php bin\console cache:clear

H:\Python\pythoncore-3.14-64\python.exe .\scripts\test_terminology_preset_r1.py
H:\Python\pythoncore-3.14-64\python.exe .\scripts\test_declarative_runtime_v1b.py
H:\Python\pythoncore-3.14-64\python.exe .\scripts\test_profile_r3b35c_contract.py

git diff --check
git status --short
```

Puis rouvrir la page PROFILE.
