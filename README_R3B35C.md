# EZStudio PROFILE R3B35C — contrat canonique genre + voix

## But

Correctif **additif** au-dessus de R3B35B. Il ne modifie aucun moteur scientifique déjà validé : CLAP, PANNs, PaSST, MERT, Madmom, métrique et tonalité restent inchangés.

### 1. Genre canonique

Ajout de :

```text
gene_registry.consensus.genre_hierarchy
profile_view.genre_hierarchy
```

Contrat :

```text
genre_family / genre / subgenre
```

La hiérarchie est une projection déterministe des candidats CLAP existants. Les scores et leur ordre ne sont pas recalculés. Aucun champ `style` n'est introduit.

### 2. Profil vocal canonique

Ajout de :

```text
gene_registry.consensus.vocal_profile
profile_view.vocal_profile
```

Dimensions séparées :

```text
lead_vocal
backing_vocals
vocal_harmonies
choir
```

Règle importante : `backing vocals`, `chant` et `vocal music` ne suffisent plus à conclure `choir=possible`. Ils restent des preuves associées, mais `choir` exige une preuve directe de chœur suffisamment convergente.

L'ancien `consensus.choirs` R3B35B est conservé temporairement pour compatibilité/historique, mais **ne doit plus être la source canonique**.

### 3. Gate STEMS

```text
vocal_profile.usable_for_stems = false
```

R3B35C reste expérimental jusqu'au benchmark humain multi-chansons. Aucune décision PROFILE ne déclenche STEMS automatiquement.

## Installation

Depuis PowerShell :

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_PROFILE_R3B35C_CANONICAL_CONTRACT.zip" -C H:\EZStudio_lab

powershell -ExecutionPolicy Bypass -File .\scripts\apply_profile_r3b35c.ps1

H:\Python\pythoncore-3.14-64\python.exe .\scripts\test_profile_r3b35c_contract.py

git diff --check
git status --short
```

Résultat attendu du test :

```text
PROFILE_R3B35C_CONTRACT_OK
```

## Re-test Breakfast

Relancer PROFILE sur **Breakfast in America** puis exporter le chromosome ADN.

Contrôles attendus :

```text
genome.pipeline_revision = profile-r3b35c-canonical-genre-vocals
environment.profile_architecture = genes-r3b35c-canonical-contract
```

Et surtout, dans `vocal_profile` pour le cas observé R3B35B :

```text
lead_vocal       -> present (AudioSet Singing convergent)
backing_vocals   -> possible (CLAP backing vocals haut classé)
choir            -> inconclusive, sauf nouvelle preuve directe convergente
```

Ce résultat correspond mieux à l'annotation humaine du run 65 : « pas vraiment [de chœurs], mais des contre-voix possibles ».

## Git

Ne pas commit/push avant le re-test Breakfast et l'examen du nouvel ADN.
