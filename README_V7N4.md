# EZChords Benchmark V7N.4 — detached worker

## Cause

`BenchmarkLauncher::launch()` utilisait `passthru()`.

Le worker Python était donc enfant synchrone de la requête HTTP Symfony.
Avec la séparation stems, le traitement dépasse 300 s et PHP coupe la
requête avec `MaxExecutionTimeError`.

Augmenter `max_execution_time` serait un mauvais correctif : un job long
ne doit pas dépendre de la durée de vie d'une requête HTTP.

## Correction

Windows :
- `cmd.exe /C start "" /B ...`
- stdout/stderr worker vers
  `H:\temp\EZChords_Benchmark\launcher\run-<id>.log`
- retour HTTP immédiat
- page du run en mode "analyse en cours"
- polling `/run/<id>/status` toutes les secondes
- progression et derniers logs lus depuis SQLite
- reload automatique quand le worker passe à `done` ou `error`

## EZScore

Aucune modification.
Aucune écriture sous `H:\EZScore`.

Le contrat V7N reste inchangé :
`H:\EZScore\analysis\stems_only.py` est seulement appelé comme code canonique,
avec toutes les sorties redirigées vers `H:\temp\EZChords_Benchmark\stems`.

## Application

```powershell
cd H:\EZChords_Benchmark

tar -xf "$env:USERPROFILE\Downloads\EZChords_Benchmark_V7N4_ASYNC_WORKER.zip" `
  -C H:\EZChords_Benchmark `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\preflight-v7n4.ps1
```

Relancer ensuite le serveur PHP et refaire une analyse.

Le run qui a dépassé 300 s peut être supprimé depuis l'interface avant le retest.
