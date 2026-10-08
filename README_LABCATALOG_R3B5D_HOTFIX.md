# EZStudio_lab — LabCatalog R3B5D hotfix

Le hotfix R3B5C a bien installé `LabCatalog.php` et son contrat a passé.
L'échec restant vient uniquement du contrôle PowerShell :

```text
debug:container ... --show-private
```

Cette option n'existe pas dans la version Symfony installée.

R3B5D ne modifie aucun code applicatif. Il remplace uniquement les scripts
`apply-labcatalog-r3b5c.ps1` et `preflight-labcatalog-r3b5c.ps1`.

Le contrôle est remplacé par :
- autoload réel de `App\Service\LabCatalog` via Composer ;
- compilation du conteneur via `cache:clear`;
- présence des routes STEMS/CHORDS via `debug:router`.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_LABCATALOG_R3B5D_HOTFIX.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\apply-labcatalog-r3b5c.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-labcatalog-r3b5c.ps1
```
