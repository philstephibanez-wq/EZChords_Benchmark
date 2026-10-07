# EZStudio_lab — Independent Application + New UI R1

## Objectif

Cette tranche transforme le runtime actif en application **EZStudio_lab autonome** et remplace l'ancien shell visuel `EZChords Benchmark` par une UI orientée laboratoire.

Principes :

```text
IMPORT
  ↓
STEMS
  ↓
CHORDS
  └─ NO-CHORD
  ↓
LYRICS
```

Diagnostics par item, pas de bloc diagnostic global.

## Indépendance

Après application :

- aucun appel runtime à `H:\EZScore`;
- aucun stockage runtime sous `H:\temp\EZChords_Benchmark`;
- STEMS est généré par `python/ezstudio/pipeline/stems/runner.py`;
- cache STEMS : `H:\temp\EZStudio_lab\stems`;
- observabilité : `H:\temp\EZStudio_lab\observability`;
- exports : `H:\temp\EZStudio_lab\exports`;
- Mongo DB : `ezstudio_lab`.

Le moteur CHORDS historique est conservé pour éviter une régression des six méthodes métriques.

## Compatibilité EZScore

On coupe les dépendances de code, pas la capacité de migration vers EZScore.

Quatre contrats versionnés sont ajoutés :

```text
contracts/stems.schema.json
contracts/chords.schema.json
contracts/lyrics.schema.json
contracts/timeline.schema.json
```

Le timebase contractuel reste :

```text
original_audio_seconds
```

L'objectif est que toute avancée validée dans EZStudio_lab puisse être promue dans EZScore quel que soit l'item.

## Correction STEMS

Le manifeste STEMS distingue désormais :

```text
duration_seconds
```

= durée réelle de l'audio, obtenue via FFprobe,

et :

```text
analysis_elapsed_seconds
```

= temps de calcul du pipeline.

Cela supprime l'ambiguïté historique où le temps de traitement pouvait être exposé comme durée audio.

## UI

Page `/` :

```text
EZStudio_lab

[ Import ] [ Stems ] [ Chords ] [ Lyrics ] [ Runs ]
```

Chaque run affiche les états :

```text
STEMS | CHORDS | N | LYRICS
```

La page `/lab/run/{id}` expose :

- STEMS ;
- CHORDS ;
- NO-CHORD ;
- LYRICS ;
- diagnostics V10 directement dans l'UI ;
- logs ;
- artefacts ;
- téléchargement du ZIP scientifique.

L'ancienne page historique reste temporairement accessible sous `/legacy`.

## Installation

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_INDEPENDENT_UI_R1.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\apply-independent-ui-r1.ps1
```

## Preflight

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-independent-ui-r1.ps1
```

Attendu en fin de sortie :

```text
EZSTUDIO_SIX_METRIC_METHODS_UNCHANGED_CONTRACT_OK
EZSTUDIO_RUNTIME_INDEPENDENCE_OK
EZSTUDIO_EZSCORE_STEMS_CONTRACT_OK
EZSTUDIO_EZSCORE_CHORDS_CONTRACT_OK
EZSTUDIO_EZSCORE_LYRICS_CONTRACT_OK
EZSTUDIO_EZSCORE_TIMELINE_CONTRACT_OK
EZSTUDIO_LAB_UI_ROUTES_OK
EZSTUDIO_NEW_UI_CONTRACT_OK
EZSTUDIO_INDEPENDENT_UI_R1_PREFLIGHT_OK
```

## Contrôle Git

```powershell
git status --short
git diff --stat
```

Ne pas utiliser `git add -A` avant recette.

## Démarrage

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

Puis :

```text
http://127.0.0.1:8701/
```

## Recette fonctionnelle

1. Vérifier le nouveau shell EZStudio_lab.
2. Ouvrir un run V10 existant : les graphiques doivent être visibles dans `Diagnostics`.
3. Lancer un nouveau run.
4. Vérifier dans les logs :
   - pipeline STEMS autonome EZStudio_lab ;
   - réutilisation du cache sous `H:\temp\EZStudio_lab\stems`;
   - aucune référence runtime à EZScore.
5. Vérifier l'export scientifique `EZStudio_Run_XXXXXX_Scientific.zip`.
6. Ne pousser qu'après cette recette.
