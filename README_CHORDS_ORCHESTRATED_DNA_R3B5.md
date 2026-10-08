# EZStudio_lab — CHORDS ORCHESTRATED DNA R3B5

Issues relues avant tranche : #2, #3, #4, #6, #7.

Construit sur le snapshot local fourni après R3B4A.

## Flux

scientific CHORDS run
→ sélection immuable chord_input / no_chord_evidence
→ benchmark execution run lié
→ analysis_jobs kind=chords_scientific
→ API LAB
→ EZS_orchestrator
→ analysis/worker_entrypoint.py
→ python/worker.py
→ python/engine.py
→ résultat canonique + ADN

## Garanties

- aucun recalcul STEMS dans le mode scientifique sélectionné ;
- SHA-256 de chaque artefact sélectionné revérifié avant consommation ;
- sélections CHORDS et NO-CHORD indépendantes ;
- six méthodes métriques conservées sur le master ;
- token interne NO-CHORD = N ;
- page CHORDS canonique toujours alimentée par le benchmark run lié ;
- le scientific run reçoit état, métriques, diagnostics, environnement et artefacts d'observabilité.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_CHORDS_ORCHESTRATED_DNA_R3B5.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\apply-chords-orchestrated-dna-r3b5.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-chords-orchestrated-dna-r3b5.ps1
```
