# EZChords Benchmark V6b — no-chord + purge

## But

Ne pas toucher aux six méthodes métriques validées R5/R6.

Le `.` représente désormais un **beat sans contenu harmonique exploitable**, pas uniquement un silence numérique du master.

Détection :
- composante harmonique HPSS ;
- RMS harmonique par beat ;
- énergie chroma par beat ;
- `.` uniquement si les deux indicateurs sont dans la zone basse du morceau.

Le résultat conserve un diagnostic :
- nombre de beats `no-chord`;
- seuil RMS;
- indices de beats silencieux.

## Purge complète locale

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\reset-benchmark.ps1
```

ou sans confirmation :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\reset-benchmark.ps1 -Force
```

Supprime :
- DB SQLite/WAL/SHM ;
- audios `public/benchmark-audio`;
- uploads/worker ;
- `results`;
- work temporaire sous `H:\temp\EZChords_Benchmark\work`.

Conserve les dépendances et caches lourds.

Après purge, la base et les tables de notation sont recréées automatiquement.

## Application

```powershell
cd H:\EZChords_Benchmark

tar -xf "$env:USERPROFILE\Downloads\EZChords_Benchmark_V6b_SILENCE_PURGE.zip" `
  -C H:\EZChords_Benchmark `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\preflight-v6b.ps1
```
