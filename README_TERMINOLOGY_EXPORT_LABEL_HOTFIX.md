# EZStudio — export label terminology hotfix

Correction visuelle uniquement :

`ZIP ADN` → `Exporter les Presets`

Le nom de fichier exporté est déjà `EZStudio_PRESET_...zip`.

Le contrat sérialisé interne du ZIP reste volontairement inchangé en R1 (`ezstudio.chromosome.adn.v2`, anciennes clés `chromosome`, `genome/*`) afin de ne pas mélanger renommage visible et migration de format.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_TERMINOLOGY_EXPORT_LABEL_HOTFIX.zip" -C H:\EZStudio_lab

powershell -ExecutionPolicy Bypass -File .\scripts\apply_terminology_export_label_hotfix.ps1

php .\scripts\test_terminology_export_label_hotfix.php

php bin\console lint:twig templates
php bin\console cache:clear

git diff --check
git status --short
```
