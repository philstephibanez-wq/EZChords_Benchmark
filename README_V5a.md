# EZChords Benchmark V5a — document root public

Cause racine trouvée dans les logs :

```text
GET /js/benchmark-player.js?v=5 -> 404
GET /benchmark-audio/run-2.mp3 -> 404
```

Le serveur PHP était lancé sans `-t public`.

`router.php` faisait bien `return false` pour les fichiers statiques, mais PHP cherchait alors ces fichiers depuis la racine du projet au lieu de `public/`.

## Correctif

Le serveur est désormais lancé avec :

```text
php -S 127.0.0.1:8701 -t H:\EZChords_Benchmark\public H:\EZChords_Benchmark\router.php
```

## Application

Arrêter le serveur puis :

```powershell
cd H:\EZChords_Benchmark

tar -xf "$env:USERPROFILE\Downloads\EZChords_Benchmark_V5a_PUBLIC_DOCROOT_FIX.zip" `
  -C H:\EZChords_Benchmark `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\preflight-v5a.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

Attendu au preflight :

```text
V5A_PUBLIC_DOCROOT_OK
V5A_PLAYER_JS_PRESENT
V5A_KEEP_UPLOADS_OK
V5A_PREFLIGHT_OK
```

Ensuite recharge la page chanson avec `Ctrl+F5`.

Les 404 sur `/js/benchmark-player.js` et `/benchmark-audio/...` doivent disparaître.
