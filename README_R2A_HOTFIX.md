# EZStudio_lab — ORCHESTRATOR LAB R2A HOTFIX

À appliquer par-dessus R2 déjà installé.

Cause de l'échec :
le test PHP exigeait le fragment source exact :

```php
'kind' => 'benchmark'
```

alors que le code réel :
- insère `benchmark` comme paramètre SQL positionnel ;
- relit ensuite la colonne `kind` ;
- l'expose dans l'enveloppe via :

```php
'kind' => (string)$job['kind']
```

R2A corrige uniquement le test contractuel. Aucun fichier de production n'est modifié.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_ORCHESTRATOR_LAB_R2A_HOTFIX.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\apply-orchestrator-lab-r2a-hotfix.ps1

powershell -ExecutionPolicy Bypass -File .\scripts\preflight-orchestrator-lab-r2a.ps1
```
