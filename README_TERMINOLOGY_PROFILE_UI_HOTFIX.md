# EZStudio — PROFILE UI terminology hotfix

Correction strictement terminologique de l'interface PROFILE.

## Modifications visibles

- `Région PROFILE du chromosome` → `Phase PROFILE de la chaîne`
- `Gène` → `Module`
- `Région` → `Phase`
- `Gènes PROFILE` → `Modules PROFILE`
- `Run ADN PROFILE` → `Run PROFILE`

Les mentions où l'ancien terme `ADN` désignait en réalité le résultat d'un run sont reformulées en `run` ou `résultat d’analyse`, afin de ne pas confondre un **Preset** (configuration) avec un **résultat**.

## Aucun changement

- aucune logique ;
- aucun moteur ;
- aucun seuil ;
- aucune route ;
- aucun schéma ;
- aucune clé persistée ;
- aucun résultat scientifique.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_TERMINOLOGY_PROFILE_UI_HOTFIX.zip" -C H:\EZStudio_lab

powershell -ExecutionPolicy Bypass -File .\scripts\apply_terminology_profile_ui_hotfix.ps1

php .\scripts\test_terminology_profile_ui_hotfix.php

php bin\console lint:twig templates
php bin\console cache:clear

git diff --check
git status --short
```
