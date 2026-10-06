# EZChords Benchmark V5b

Ajouts/corrections :
- volumes MP3 et MIDI indépendants ;
- Stop remet toutes les timelines à gauche et efface tous les highlights ;
- le scroll manuel d'une timeline n'est plus forcé vers le beat courant quand la lecture est arrêtée ;
- après seek MP3, la position choisie est conservée ;
- navigation avec Bilan ;
- page Bilan globale et détaillée ;
- correction du faux accord lorsqu'un beat n'a aucun recouvrement avec un segment harmonique ;
- correctif V5a `-t public` conservé.

Application :

```powershell
cd H:\EZChords_Benchmark
tar -xf "$env:USERPROFILE\Downloads\EZChords_Benchmark_V5b_REPORT_VOLUMES_STOP_SILENCE.zip" `
  -C H:\EZChords_Benchmark `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\preflight-v5b.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\recette.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

Une nouvelle analyse est nécessaire pour voir la correction des silences dans les nouvelles grilles.
