# EZChords_Benchmark V1c — Console + recette hotfix

Ce correctif traite les deux erreurs de la recette Windows :

1. `Symfony\Component\Console\Application` absent :
   `symfony/console` n'était pas déclaré.
2. `ENGINE_SELF_TEST_SKIPPED` :
   la recette cherchait `benchmark_engine.py` au lieu du vrai moteur `python\engine.py`.

## Application

```powershell
cd H:\EZChords_Benchmark

tar -xf "$env:USERPROFILE\Downloads\EZChords_Benchmark_V1c_CONSOLE_RECETTE_HOTFIX.zip" `
  -C H:\EZChords_Benchmark `
  --strip-components=1
```

Puis :

```powershell
composer update symfony/console --with-dependencies
```

Puis :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\recette.ps1
```

Attendu :

```text
PHP_APP_LINT_OK
PYTHON_COMPILE_OK
ENGINE_SELF_TEST_OK
...
RECETTE_OK
```

Aucune logique benchmark n'est modifiée.
