# EZChords Benchmark V6 — priorité algorithmes

Ce patch ne cherche pas à créer artificiellement des résultats différents.

Il corrige un biais structurel du benchmark :

- jusqu'ici, la signature Auto était choisie avant Beat This ;
- toutes les méthodes utilisaient ensuite cette même période ;
- si Auto choisissait 2/4, seulement deux phases étaient comparées ;
- cela pouvait masquer les divergences visibles en 4/4.

## V6

- tous les scores de phase P0…Pn sont conservés par méthode ;
- en Auto uniquement, l'ambiguïté 2/4 ↔ 4/4 est raffinée avec le signal downbeat Beat This ;
- si la signature est imposée manuellement, elle n'est jamais modifiée ;
- le résultat stocke :
  - signature initiale ;
  - signature raffinée ;
  - delta BeatThis 4/4 - 2/4 ;
  - scores de toutes les phases ;
  - histogramme de convergence des six méthodes ;
- la page chanson affiche ces diagnostics.

## Application

```powershell
cd H:\EZChords_Benchmark

tar -xf "$env:USERPROFILE\Downloads\EZChords_Benchmark_V6_ALGO_CORE.zip" `
  -C H:\EZChords_Benchmark `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\recette.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

Une nouvelle analyse est nécessaire : les anciens runs ne contiennent pas les diagnostics V6.
