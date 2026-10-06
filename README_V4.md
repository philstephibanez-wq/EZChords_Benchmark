# EZChords_Benchmark V4 — player synchronisé MP3 + SoundFont

Périmètre strictement benchmark. **Aucun fichier EZScore n'est modifié.**

## Ajouts

Pour une chanson analysée :

- MP3 original conservé localement ;
- checkbox MP3 ON/OFF ;
- un seul algorithme sélectionné pour l'écoute ;
- une timeline compacte par algorithme ;
- beat courant surligné visuellement ;
- clic sur un beat => seek ;
- autoscroll de la timeline ;
- piano virtuel invisible ;
- SoundFont `acoustic_grand_piano` ;
- aucun fichier MIDI ;
- aucune nouvelle analyse MIDI/harmonique ;
- les accords sont lus exclusivement depuis la timeline sélectionnée ;
- **un accord est rejoué à chaque beat** ;
- `.` / `N` = silence ;
- `-` = répétition de l'accord précédent ;
- MP3 + SoundFont + highlight utilisent la même horloge du player audio.

Le piano SoundFont est chargé par le navigateur via `soundfont-player`.
La première utilisation nécessite donc un accès Internet.

## Compatibilité

Les nouvelles analyses conservent désormais l'audio source (`keepUploads=true`).

Les anciennes analyses dont l'audio a déjà été supprimé restent consultables, mais leur player indique que l'audio source est absent. Il faudra réimporter uniquement ces morceaux si on veut les écouter.

## Application

Arrêter le serveur courant avec `Ctrl+C`, puis :

```powershell
cd H:\EZChords_Benchmark

tar -xf "$env:USERPROFILE\Downloads\EZChords_Benchmark_V4_PLAYER.zip" `
  -C H:\EZChords_Benchmark `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\recette.ps1

powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

## Git

Après validation fonctionnelle :

```powershell
git status --short
git add .
git commit -m "Add synchronized benchmark timeline player"
git push
```
