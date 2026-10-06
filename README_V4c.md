# EZChords_Benchmark V4c — reset + attente visible

Ce patch ajoute uniquement :

- une attente visible pendant l'analyse synchrone ;
- un compteur de temps écoulé ;
- un script pour repartir à neuf sur les données du benchmark.

Aucun scheduler, aucune queue, aucun polling.
Aucune modification EZScore.

## Application

```powershell
cd H:\EZChords_Benchmark

tar -xf "$env:USERPROFILE\Downloads\EZChords_Benchmark_V4c_RESET_WAIT.zip" `
  -C H:\EZChords_Benchmark `
  --strip-components=1
```

## Reset complet du benchmark

Arrêter d'abord le serveur avec `Ctrl+C`, puis :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\reset-benchmark.ps1
```

Le script demande de taper :

```text
RESET
```

Il supprime uniquement :

```text
data\benchmark.sqlite
data\benchmark.sqlite-wal
data\benchmark.sqlite-shm
var\uploads
var\worker
results\*
```

Puis redémarrer :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\recette.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
```
