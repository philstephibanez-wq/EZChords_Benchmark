# EZChords Benchmark V4g — réécriture forcée des fichiers critiques

Les logs montrent que V4f n'était pas réellement servi :

```text
GET /js/benchmark-player.js -> 404
Player V4f absent
ancien bench_audio encore actif
```

V4g ne rajoute pas de fonctionnalité. Il force uniquement les fichiers critiques et vérifie l'état réel du working tree.

## Application

Arrêter le serveur (`Ctrl+C`), puis :

```powershell
cd H:\EZChords_Benchmark

tar -xf "$env:USERPROFILE\Downloads\EZChords_Benchmark_V4g_FORCE_CRITICAL_FILES.zip" `
  -C H:\EZChords_Benchmark `
  --strip-components=1
```

Puis exécuter **avant toute recette ou démarrage** :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-v4g.ps1
```

Le résultat attendu est :

```text
V4G_CRITICAL_FILES_OK
V4G_CACHE_OK
V4G_PREFLIGHT_OK
```

Ensuite :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\recette.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

Sur la page chanson, vérifier d'abord :

```text
Player V4g
Niveau [Débutant | Intermédiaire | Confirmé]
```

Et dans les logs serveur, il ne doit plus y avoir :

```text
GET /js/benchmark-player.js - No such file or directory
```
