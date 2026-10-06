# EZChords_Benchmark V2

Patch V2 à appliquer sur la V1c déjà installée.

## Ce que corrige / ajoute V2

- corrige le crash du `router.php` avec Symfony Runtime et `php -S`;
- timeline compacte horizontale par algorithme;
- case à cocher d'approbation par algorithme;
- état `non revu` distinct de `rejeté`;
- persistance SQLite des revues;
- score global multi-chansons;
- grille détaillée conservée en volet repliable;
- bouton `Préparer publication GitHub`;
- génération de `results/index.json`;
- génération par run de :
  - `result.json`
  - `timeline.json`
  - `benchmark.html`
- aucune donnée audio publiée;
- moteur explicitement `master_audio`;
- aucune dépendance aux stems;
- JSON moteur enrichi avec :
  - beat-grid complet
  - durée
  - versions
  - paramètres
  - segments accords
  - source d'analyse

## Application

Depuis :

```powershell
cd H:\EZChords_Benchmark
```

Appliquer :

```powershell
tar -xf "$env:USERPROFILE\Downloads\EZChords_Benchmark_V2.zip" `
  -C H:\EZChords_Benchmark `
  --strip-components=1
```

Puis recette :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\recette.ps1
```

Puis lancement :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

Ouvrir :

```text
http://127.0.0.1:8701
```

## Migration SQLite

Aucune commande Doctrine.

La migration est additive et automatique au premier accès :
- `run_reviews`
- `algorithm_reviews`

Les anciennes analyses restent présentes.

## Revue

Pour une chanson :
- cocher les algorithmes approuvés;
- laisser décochés les algorithmes rejetés;
- cliquer `Enregistrer mes choix`.

Avant le premier enregistrement, tous les algorithmes sont `non revu`.

Le score global est :

```text
approbations / revues × 100
```

Le dénominateur est affiché.

## Publication GitHub

Le bouton `Préparer publication GitHub` écrit sous :

```text
results/
```

Il ne pousse rien.

Ensuite, le propriétaire du repo reste maître du push :

```powershell
git add results
git commit -m "Add benchmark results"
git push
```

## Recette effectuée avant livraison

- PHP lint sur les fichiers V2 : OK
- Python `py_compile` : OK
- `ENGINE_SELF_TEST_OK`
- JSON payload publisher : validation statique OK
- ZIP integrity : OK

Limite : le démarrage Symfony Runtime avec le `php -S` Windows cible reste à confirmer sur la machine cible.
