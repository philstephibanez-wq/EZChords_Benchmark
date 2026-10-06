# EZChords Benchmark V4b — audio/synth unblocked

Corrige le cas où aucun son ne sortait.

Cause principale de conception :
le bouton de lecture attendait le chargement du SoundFont avant de lancer le MP3.
Un chargement SoundFont réseau lent ou bloqué bloquait donc aussi le MP3.

## V4b

- MP3 démarre immédiatement au clic ;
- SoundFont charge en parallèle ;
- lecteur HTML natif visible avec play/seek/volume ;
- état du synthé affiché ;
- erreurs MP3/SoundFont affichées dans la page ;
- MP3 reste l'horloge maître quand il existe ;
- aucune modification EZScore.

## Application

```powershell
cd H:\EZChords_Benchmark

tar -xf "$env:USERPROFILE\Downloads\EZChords_Benchmark_V4b_AUDIO_FIX.zip" `
  -C H:\EZChords_Benchmark `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\recette.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
```
