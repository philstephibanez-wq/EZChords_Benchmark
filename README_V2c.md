# EZChords_Benchmark V2c — DEV cache fix

Cause du crash :

```text
App\Service\BenchmarkLauncher::__construct():
Argument #1 ($database) must be of type App\Service\Database, string given
```

Le stacktrace pointait vers :

```text
var\cache\dev\...
```

alors que la recette V2b validait le conteneur `prod`.

Le serveur local tourne en `dev`, donc il utilisait encore un ancien conteneur compilé avant la modification du constructeur.

## Application

Arrêter le serveur (`Ctrl+C`) puis :

```powershell
cd H:\EZChords_Benchmark

tar -xf "$env:USERPROFILE\Downloads\EZChords_Benchmark_V2c_DEV_CACHE_FIX.zip" `
  -C H:\EZChords_Benchmark `
  --strip-components=1
```

Puis :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\recette.ps1
```

La recette contrôle maintenant **prod et dev**.

Puis :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

Le démarrage reconstruit explicitement `var\cache\dev` avant `php -S`.
