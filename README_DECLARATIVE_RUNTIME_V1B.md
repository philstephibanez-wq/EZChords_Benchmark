# EZStudio — Declarative Runtime V1B

## But

Brancher réellement le gène PROFILE `semantic.clap-open-vocabulary` sur le runtime déclaratif commun, sans mutation scientifique.

## Garantie de non-régression

La Gene Spec active est toujours :

`adn/specs/profile/semantic.clap-open-vocabulary.r3b35c.json`

Elle reprend le contrat R3B35C :

- même modèle CLAP ;
- même sample rate ;
- même chunking ;
- mêmes taxonomies ;
- mêmes templates de prompts ;
- même `category_relative_softmax` ;
- mêmes top-k.

Le fichier legacy `python/ezstudio/pipeline/profile/semantic_clap.py` n'est pas modifié. Il reste disponible comme référence pour les comparaisons d'équivalence.

CHORDS/N n'est pas touché.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_DECLARATIVE_RUNTIME_V1B.zip" -C H:\EZStudio_lab

powershell -ExecutionPolicy Bypass -File .\scripts\apply_declarative_runtime_v1b.ps1

H:\Python\pythoncore-3.14-64\python.exe .\scripts\test_declarative_runtime_v1b.py

H:\Python\pythoncore-3.14-64\python.exe .\scripts\test_declarative_runtime_v1a.py

H:\Python\pythoncore-3.14-64\python.exe .\scripts\test_profile_r3b35c_contract.py

git diff --check
git status --short
```

## Résultat attendu

`DECLARATIVE_RUNTIME_V1B_CONTRACT_OK`

Après validation de V1B, lancer un PROFILE de référence permettra de contrôler l'équivalence réelle GPU/ADN avec R3B35C avant la première mutation déclarative.
