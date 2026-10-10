# EZStudio — TERMINOLOGY PRESET R1 REGISTRY PROPERTY HOTFIX

## Problème

Après le premier hotfix, certains constructeurs injectaient correctement :

```php
private readonly AnalysisRunRegistry $runRegistry
```

mais leurs méthodes contenaient encore :

```php
$this->runs->...
```

Cela provoquait notamment dans PROFILE :

```text
Undefined property: App\Service\ProfileDnaExecutionService::$runs
```

## Correction

Tous les accès d'objet issus du renommage R1 deviennent :

```php
$this->runRegistry->...
```

Le correctif vérifie globalement `src/**/*.php` pour empêcher :
- `AnalysisRunRegistry $runs`
- `$this->runs->...`

Le script R1 d'origine est également durci.

Aucune logique scientifique n'est modifiée.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_TERMINOLOGY_PRESET_R1_REGISTRY_PROPERTY_HOTFIX.zip" -C H:\EZStudio_lab

powershell -ExecutionPolicy Bypass -File .\scripts\apply_terminology_preset_r1_registry_property_hotfix.ps1

php .\scripts\test_terminology_preset_r1_registry_property_hotfix.php

php bin\console lint:container
php bin\console cache:clear

H:\Python\pythoncore-3.14-64\python.exe .\scripts\test_terminology_preset_r1.py
H:\Python\pythoncore-3.14-64\python.exe .\scripts\test_declarative_runtime_v1b.py
H:\Python\pythoncore-3.14-64\python.exe .\scripts\test_profile_r3b35c_contract.py

git diff --check
git status --short
```

Puis relancer PROFILE depuis l'interface.
