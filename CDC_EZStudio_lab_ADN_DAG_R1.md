# CDC — EZStudio_lab
## ADN scientifique, DAG de dépendances et versionnement expérimental
Version R1

## 1. Finalité

EZStudio_lab doit permettre d'améliorer progressivement la fiabilité de :

- STEMS ;
- CHORDS ;
- NO-CHORD ;
- LYRICS.

Le laboratoire doit conserver l'ADN complet de chaque résultat afin de pouvoir expliquer, reproduire et comparer toute analyse.

Principe contractuel :

> Toute modification d'une entrée, d'une sélection de stems, d'un moteur, d'un modèle, d'un paramètre ou d'un critère crée un nouveau run immuable. Aucun résultat scientifique n'est écrasé.

---

## 2. Modèle général

```text
IMPORT
  ↓
STEMS #A / #B / #C
  ↓
sélections de stems versionnées
  ↓
CHORDS #D / #E / #F
  ├─ NO-CHORD
  ↓
LYRICS #G / #H / #I
```

Le résultat réel est un DAG, pas une chaîne unique.

Exemple :

```text
IMPORT #10
  │
  ├─ STEMS #42
  │   ├─ sélection A
  │   │   └─ CHORDS #51
  │   │       ├─ NO-CHORD config N1
  │   │       └─ LYRICS #60
  │   │
  │   └─ sélection B
  │       └─ CHORDS #52
  │           ├─ NO-CHORD config N2
  │           ├─ LYRICS #61
  │           └─ LYRICS #62
  │
  └─ STEMS #47
      └─ sélection C
          └─ CHORDS #70
              └─ LYRICS #71
```

---

## 3. Run scientifique immuable

Chaque run conserve au minimum :

- `run_id` ;
- `item` ;
- parent(s) ;
- artifact_id(s) ;
- hashes ;
- moteur ;
- modèle ;
- checkpoint ;
- versions ;
- paramètres ;
- critères de décision ;
- métriques ;
- diagnostics ;
- environnement Python/Torch/CUDA ;
- GPU / VRAM / temps ;
- validation humaine ;
- logs ;
- statut ;
- date de création.

Une ré-analyse crée un nouveau run.

---

## 4. STEMS

Une chanson peut posséder plusieurs runs STEMS.

Exemple :

```text
Aline
 ├─ STEMS #42 — RoFormer / config A
 ├─ STEMS #47 — RoFormer / config B
 └─ STEMS #55 — Demucs / config C
```

Chaque run STEMS conserve son ADN complet :

```text
source_audio_hash
engine
model
checkpoint
engine_version
parameters
chunk
overlap
precision
device
torch_version
cuda_version
gpu
elapsed_time
peak_vram
stem taxonomy
instrument recognition config
quality metrics
leakage metrics
artifact hashes
diagnostics
human validation
```

Chaque stem publié devient un artefact versionné :

```text
lead_vocals
backing_vocals
drums
bass
guitar
piano
other
```

avec :
- `artifact_id` ;
- hash ;
- chemin ;
- rôle ;
- run parent.

---

## 5. Sélections de stems versionnées pour CHORDS

Le choix des stems fait partie de l'ADN CHORDS.

Exemple A :

```text
STEMS #42

CHORD INPUTS
[✓] bass
[✓] guitar
[✓] piano
[✓] other
[ ] drums
[ ] lead_vocals
[ ] backing_vocals

→ CHORDS #51
```

Exemple B :

```text
STEMS #42

CHORD INPUTS
[✓] bass
[✓] guitar
[ ] piano
[ ] other
[ ] drums
[ ] lead_vocals
[ ] backing_vocals

→ CHORDS #52
```

Les deux résultats coexistent.

La sélection enregistre :

```text
parent_stems_run_id
selected_artifact_ids
selected_artifact_hashes
selection_role
selection_version
```

---

## 6. CHORDS

Un run CHORDS dépend explicitement de :

- la chanson ;
- un run STEMS parent ;
- une sélection de stems ;
- un moteur d'accords ;
- une configuration métrique ;
- une configuration de projection beat ;
- une configuration NO-CHORD.

ADN CHORDS :

```text
parent_stems_run_id
chord_input_artifact_ids
chord_input_hashes
engine
engine_version
model
parameters
raw chord output
normalized chord output
beat grid
projection rules
snapping tolerance
six metric methods
phase scores
selected metric method
diagnostics
human validation
```

Les six méthodes historiques restent conservées :

1. Beat This downbeat ;
2. Percussive onset ;
3. Bass CQT ;
4. Rhythm + Bass ;
5. Harmonic novelty ;
6. R41-like fusion.

---

## 7. NO-CHORD

NO-CHORD reste un sous-domaine de CHORDS.

La classe interne reste :

```text
N
```

Les stems utilisés pour CHORDS peuvent différer des stems utilisés comme preuves NO-CHORD.

Exemple :

```text
CHORD INPUTS
[✓] bass
[✓] guitar
[✓] piano
[✓] other

NO-CHORD HARMONIC EVIDENCE
[✓] bass
[✓] guitar
[✓] piano
[✓] other

EXCLUDED FROM HARMONIC SUPPORT
[✓] drums
[✓] lead_vocals
[✓] backing_vocals
```

ADN NO-CHORD :

```text
parent_chords_run_id
parent_stems_run_id
evidence_artifact_ids
excluded_artifact_ids
variant
thresholds
support_count
supporting_stems
harmonic activity
transition rules
confidence/posterior
diagnostics
human validation
```

---

## 8. LYRICS

LYRICS suit exactement le même modèle de provenance.

Un run LYRICS peut dépendre :

- d'un run STEMS pour `lead_vocals` ;
- d'un run CHORDS pour beat grid / chord grid ;
- d'un moteur ASR ;
- d'un VAD ;
- d'un aligner ;
- d'une configuration temporelle.

Exemple :

```text
STEMS #42
  └─ lead_vocals

CHORDS #52
  └─ beat_grid

LYRICS #60
  ├─ source = lead_vocals de STEMS #42
  ├─ timing = beat_grid de CHORDS #52
  ├─ Whisper large-v3-turbo
  ├─ VAD X
  └─ aligner Y
```

ADN LYRICS :

```text
parent_stems_run_id
vocal_artifact_id
parent_chords_run_id
beat_grid_artifact_id
chord_grid_artifact_id
asr_engine
asr_model
asr_version
vad_engine
vad_parameters
aligner
aligner_version
language
pre_roll
timebase
compute_type
device
diagnostics
timing metrics
WER/CER
human validation
```

---

## 9. Cartographie ADN

Chaque run doit fournir une cartographie de son ascendance.

Exemple :

```text
LYRICS #71
 ├─ Whisper / config
 ├─ VAD / aligner
 ├─ CHORDS #70
 │   ├─ sélection stems C
 │   ├─ moteur accords
 │   ├─ métrique
 │   └─ NO-CHORD
 │       └─ preuves harmoniques
 └─ STEMS #47
     ├─ moteur
     ├─ modèle
     ├─ paramètres
     ├─ diagnostics
     └─ lead_vocals artifact
```

Chaque nœud doit être cliquable.

---

## 10. Validation humaine

La validation humaine fait partie des données expérimentales.

Elle peut porter sur :

- qualité d'un stem ;
- leakage ;
- accord correct / incorrect ;
- downbeat correct / incorrect ;
- No-Chord correct / incorrect ;
- timing lyrics ;
- transcription ;
- commentaire libre.

Le LAB doit croiser :

```text
validation humaine
+
métriques objectives
+
paramètres
+
provenance
```

---

## 11. Comparaison intra-chanson

Pour une même chanson :

```text
STEMS #42 vs #47
CHORDS #51 vs #52 vs #70
NO-CHORD config N1 vs N2
LYRICS #60 vs #61 vs #62
```

Comparaisons :

- moteurs ;
- sélections de stems ;
- paramètres ;
- métriques ;
- diagnostics ;
- validations humaines ;
- temps ;
- VRAM ;
- artefacts.

---

## 12. Comparaison inter-chansons

Le laboratoire doit agréger les performances sur plusieurs chansons.

Objectif :

> rechercher la configuration la plus robuste globalement, pas celle qui optimise un seul morceau.

Exemple :

```text
Configuration A
Aline       94 %
Susanna     71 %
La Bohème   89 %

Configuration B
Aline       90 %
Susanna     88 %
La Bohème   87 %
```

Une configuration légèrement moins bonne sur le meilleur cas peut être préférée si elle est nettement plus stable.

Métriques globales :

- nombre de chansons ;
- nombre de runs ;
- moyenne ;
- médiane ;
- variance ;
- écart-type ;
- P10 / P50 / P90 ;
- worst-case ;
- taux de validation humaine ;
- taux d'erreur ;
- temps moyen ;
- VRAM ;
- stabilité selon type de morceau.

---

## 13. Recherche du meilleur compromis

Le choix final ne doit pas être mono-métrique.

Critères :

```text
qualité musicale
+ validation humaine
+ précision objective
+ robustesse inter-chansons
+ faible variance
+ coût GPU
+ temps de calcul
+ reproductibilité
```

La décision finale doit être explicable à partir de l'ADN.

---

## 14. Catalogue / Home

La page d'accueil est le catalogue des chansons analysées.

Pour chaque chanson :

```text
Titre / Artiste
STEMS : N runs
CHORDS : N runs
LYRICS : N runs
Dernier run
État
Actions
```

Actions :

- STEMS ;
- CHORDS ;
- RUN ;
- historique ;
- comparaison ;
- corbeille.

---

## 15. Suppression en cascade

Supprimer une chanson doit supprimer toute sa descendance :

```text
song
├─ runs STEMS
├─ runs CHORDS
├─ runs NO-CHORD
├─ runs LYRICS
├─ jobs techniques
├─ artefacts
├─ diagnostics
├─ logs
└─ exports
```

Contraintes :

- confirmation explicite ;
- refus si un job est actif ;
- aucune suppression d'un artefact partagé avec une autre chanson/hash.

---

## 16. Orchestrator

L'orchestrator est uniquement responsable de l'exécution technique.

Il ne choisit jamais :

- moteur ;
- stems ;
- paramètres ;
- critères scientifiques.

```text
run scientifique figé
        ↓
job technique
        ↓
EZS_orchestrator
        ↓
worker
        ↓
progress / complete / fail
```

---

## 17. Ergonomie du DAG

L'arbre peut devenir complexe. Cette complexité est nécessaire scientifiquement mais ne doit pas rendre l'UI illisible.

L'interface doit proposer au minimum :

- vue simplifiée par défaut ;
- branche active mise en évidence ;
- filtres par item ;
- filtres par moteur/configuration ;
- réduction/extension des branches ;
- comparaison de deux branches ;
- affichage ADN complet à la demande ;
- navigation directe vers parent/enfant ;
- labels lisibles et noms humains en complément des IDs ;
- possibilité de marquer une branche comme référence.

La complexité doit rester dans le modèle scientifique ; l'interface doit la rendre navigable.

---

## 18. Critères d'acceptation principaux

- plusieurs runs STEMS par chanson ;
- plusieurs sélections de stems versionnées ;
- plusieurs runs CHORDS issus du même run STEMS ;
- plusieurs configurations NO-CHORD ;
- plusieurs runs LYRICS ;
- lineage complet ;
- artifact_id + hash sur chaque dépendance ;
- aucune réanalyse destructive ;
- comparaison intra-chanson ;
- comparaison inter-chansons ;
- validation humaine persistée ;
- cartographie ADN cliquable ;
- reproductibilité exacte d'un run ;
- possibilité d'identifier le meilleur compromis global sur le corpus.
