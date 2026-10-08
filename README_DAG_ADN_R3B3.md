# EZStudio_lab — DAG ADN R3B3

Issues relues avant tranche : #2, #3, #4, #5, #6, #7.

Cette tranche pose le socle de données du CDC ADN/DAG sans modifier les moteurs existants.

## Ajouts

Tables additives :
- `scientific_runs`
- `scientific_run_parents`
- `scientific_artifacts`
- `scientific_run_inputs`
- `scientific_run_aliases`
- `scientific_run_labels`

Le modèle permet :
- plusieurs runs STEMS par chanson ;
- plusieurs runs CHORDS issus d'un même run STEMS ;
- plusieurs sélections d'artefacts/stems via `scientific_run_inputs` ;
- rôles distincts comme `chord_input`, `no_chord_evidence`, `lyrics_audio`, `timing_context` ;
- plusieurs runs LYRICS issus d'une branche donnée ;
- artifact_id + SHA-256 ;
- lineage parent/enfant ;
- comparaison inter-chansons par moteur/version/modèle ;
- export JSON de l'ADN d'un run.

## Routes ajoutées

- `/dna/song/{id}` : branches scientifiques d'une chanson ;
- `/dna/run/{id}` : ADN complet ;
- `/dna/run/{id}.json` : ADN + lineage machine-readable ;
- `/dna/compare/{item}` : agrégation STEMS/CHORDS/LYRICS inter-chansons.

## Important

Cette tranche ne modifie PAS :
- le moteur CHORDS ;
- les six méthodes métriques ;
- NO-CHORD ;
- le worker ;
- l'orchestrator ;
- les vues CHORDS et RUN validées.

Elle fournit le registre scientifique nécessaire pour la tranche suivante :
1. enregistrer chaque run STEMS réel dans `scientific_runs` ;
2. publier chaque stem comme `scientific_artifact` ;
3. écran CHORDS de sélection de run STEMS parent ;
4. cases à cocher versionnées pour `chord_input` et `no_chord_evidence` ;
5. création d'un nouveau run CHORDS au lieu d'écraser l'ancien.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_DAG_ADN_R3B3.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\apply-dag-adn-r3b3.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-dag-adn-r3b3.ps1
```
