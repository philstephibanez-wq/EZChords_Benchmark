# EZStudio_lab — STEMS -> CHORDS DNA R3B4

Issues relues avant tranche : #2, #3, #4, #6, #7.

## Ce qui devient réel dans cette tranche

### 1. STEMS -> registre ADN

Chaque analyse STEMS lancée depuis l'UI crée désormais immédiatement un `scientific_run`.

Quand le job STEMS se termine :
- le run scientifique passe à `done` ;
- `lead_vocals`, `backing_vocals`, `drums`, `bass`, `guitar`, `piano`, `other`
  sont enregistrés comme `scientific_artifacts` ;
- chaque artefact reçoit son SHA-256 ;
- le job technique est lié au run scientifique par alias ;
- manifest / diagnostics / environnement sont rattachés au run.

Les anciens jobs R3B2 peuvent être synchronisés au chargement de la page STEMS.

### 2. Matrice CHORDS / NO-CHORD versionnée

Nouvelle page :
`/chords/experiment?‌song=<id>`

Pour un run STEMS terminé, l'utilisateur choisit séparément :
- les artefacts consommés par CHORDS (`chord_input`) ;
- les artefacts utilisés comme preuves harmoniques NO-CHORD (`no_chord_evidence`).

Toute sélection produit un nouveau `scientific_run` CHORDS immuable.

Le run contient :
- `parent_stems_run_id` ;
- artifact_id + SHA-256 exacts ;
- sélection CHORDS ;
- sélection NO-CHORD ;
- exclusions ;
- moteur ;
- signature ;
- contrat des six méthodes historiques ;
- `N` comme token interne.

Un `request.json` machine-readable est publié sous :
`H:\temp\EZStudio_lab\chords\scientific-run-XXXXXX\request.json`

### 3. Historique

La page CHORDS affiche :
- les runs ADN configurés ;
- les analyses historiques existantes ;
- les liens vers la page CHORDS canonique `bench_view`.

## Important — frontière de cette tranche

Cette tranche versionne réellement la sélection et produit le contrat d'exécution exact,
mais **ne branche pas encore ce request.json au worker CHORDS orchestré**.

C'est volontaire : l'entrypoint/launcher LAB local est plus récent que le default branch GitHub.
Le moteur CHORDS existant n'est donc pas modifié à l'aveugle.

La prochaine tranche est uniquement le bridge d'exécution :
`scientific CHORDS run -> analysis_job -> orchestrator -> worker_entrypoint -> engine`
avec consommation des artefacts sélectionnés, sans recalcul STEMS.

## Non-régression

Aucune modification de :
- six méthodes métriques ;
- moteur lv-chordia ;
- politique N actuelle ;
- page `bench_view` ;
- page `lab_run` ;
- mutex GPU / orchestrator.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_STEMS_CHORDS_DNA_R3B4.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\apply-stems-chords-dna-r3b4.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-stems-chords-dna-r3b4.ps1
```
