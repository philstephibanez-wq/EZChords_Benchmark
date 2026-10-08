# EZStudio_lab — NAV ACTIVE R3A3

Lecture préalable des issues #3, #4, #5, #6 et #7.

Correctif limité à la navigation visuelle du pipeline.

Comportement :
- l'onglet actif est clairement inversé dans le header ;
- `aria-current="page"` est appliqué ;
- sur le Workbench racine, l'état actif suit :
  - le hash `#import/#stems/#chords/#lyrics/#runs` ;
  - le clic ;
  - la section réellement visible pendant le scroll ;
- aucun changement pipeline, worker, orchestrator, données ou moteurs.

Application :

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_NAV_ACTIVE_R3A3.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\apply-nav-active-r3a3.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-nav-active-r3a3.ps1
```
