# EZStudio_lab — ORCHESTRATOR LAB R2B HOTFIX

R2A avait une erreur de syntaxe dans le test PHP lui-même :
une chaîne PHP double-quoted contenait `$job['kind']`, ce qui déclenchait
l'interpolation PHP et produisait le parse error.

R2B remplace cette assertion par deux assertions sûres :
- `"'kind' => (string)"`
- `"\$job['kind']"`

Aucun fichier de production n'est modifié.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_ORCHESTRATOR_LAB_R2B_HOTFIX.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\apply-orchestrator-lab-r2b-hotfix.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-orchestrator-lab-r2b.ps1
```
