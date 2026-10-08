# EZStudio_lab — ORCHESTRATOR READ-ONLY R2C + RESET R1E

Ce livrable ne modifie **aucun fichier** de `H:\EZS_orchestrator`.

Il fait trois choses :

1. supprime d'EZStudio_lab les workers locaux / essais d'intégration rejetés ;
2. remet à zéro toutes les données historiques EZStudio_lab ;
3. vérifie le contrat réel de l'orchestrator en lecture seule.

Le preflight vérifie que l'orchestrator courant ne publie que les targets
`DEV` et `PROD`, et que son planner exécute un entrypoint appartenant à la
target configurée.

C'est une contrainte importante : avec ce contrat courant, le worker permanent
ne peut pas exécuter directement `H:\EZStudio_lab\analysis\...` sans changement
côté orchestrator ou côté target DEV/PROD. R2C ne contourne pas ce garde-fou.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_ORCHESTRATOR_READONLY_R2C_RESET.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\cleanup-rejected-orchestrator-integration-r2c.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\reset-history-r1.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-orchestrator-readonly-r2c.ps1
```

Le reset ne touche ni `H:\EZS_orchestrator`, ni ses historiques DEV/PROD.
