# EZChords_Benchmark V4a — player visible même sans MP3

Corrige le cas montré sur les anciennes analyses :

- le bouton ▶ est maintenant visible sur chaque algorithme même si l'audio source a disparu ;
- Play/Pause/Stop sont toujours visibles en haut ;
- sans MP3, la timeline et le piano SoundFont fonctionnent avec une horloge interne ;
- avec MP3, le MP3 reste l'horloge maître ;
- le checkbox MP3 est désactivé quand l'ancien fichier audio n'existe plus ;
- aucune nouvelle analyse harmonique.

## Application

```powershell
cd H:\EZChords_Benchmark

tar -xf "$env:USERPROFILE\Downloads\EZChords_Benchmark_V4a_PLAYER_NOAUDIO_FIX.zip" `
  -C H:\EZChords_Benchmark `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\recette.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

Pour voir aussi le MP3 original, il faut une analyse effectuée depuis V4/V4a, car les analyses plus anciennes pouvaient supprimer l'upload audio.
