# EZStudio_lab — LabCatalog R3B5C hotfix

## Cause exacte

`StemsLabController` et `ChordsExperimentController` injectent `App\Service\LabCatalog`,
mais `src/Service/LabCatalog.php` n'était pas inclus dans les tranches R3B4/R3B5.

Symfony découvre les routes, puis échoue à l'exécution du contrôleur avec :

`type-hinted with the non-existent class or interface "App\Service\LabCatalog"`

Le hotfix réinstalle le `LabCatalog` déjà introduit dans R3B2.

Aucun moteur audio, worker, schéma ADN ni orchestration n'est modifié.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_LABCATALOG_R3B5C_HOTFIX.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\apply-labcatalog-r3b5c.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-labcatalog-r3b5c.ps1
```

Après validation, recharger `/chords/experiment`.
