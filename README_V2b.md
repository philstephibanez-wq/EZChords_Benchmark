# EZChords_Benchmark V2b — BENCH_PYTHON fix

Le V2a ne suffisait pas : Symfony continuait à résoudre `BENCH_PYTHON` au POST `/run`.

V2b rend le launcher indépendant des variables d'environnement :

- `BenchmarkLauncher` a des valeurs canoniques explicites ;
- `config/services.yaml` ne contient plus aucun `%env(...)%` ;
- `start.ps1` exporte quand même `BENCH_PYTHON`, `BENCH_DEP_ROOT`, `KEEP_UPLOADS` comme garde-fou ;
- la recette vérifie explicitement l'absence de `%env(` et inspecte le service compilé.

## Application

Arrêter le serveur actuel avec `Ctrl+C`, puis :

```powershell
cd H:\EZChords_Benchmark

tar -xf "$env:USERPROFILE\Downloads\EZChords_Benchmark_V2b_BENCH_PYTHON_FIX.zip" `
  -C H:\EZChords_Benchmark `
  --strip-components=1
```

Puis :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\recette.ps1
```

Puis :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

Au démarrage, le script doit afficher :

```text
BENCH_PYTHON=H:\Python\pythoncore-3.14-64\python.exe
BENCH_DEP_ROOT=H:\temp\EZChords_Benchmark\deps
KEEP_UPLOADS=0
```

Ensuite relancer une analyse.
