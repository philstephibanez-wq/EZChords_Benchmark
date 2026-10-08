# EZStudio_lab — CHORDS UI R2C

Correctif ciblé de la vue historique Benchmark/CHORDS.

Cause :
le template continue à émettre les classes historiques du player et des timelines,
mais la refonte `base.html.twig` du LAB a supprimé leur CSS spécifique.

R2C restaure ces styles localement dans :

```text
templates/benchmark/view.html.twig
```

via le point d'extension existant :

```twig
{% block styles %}
```

Aucun changement :
- analyse ;
- données ;
- contrôleurs ;
- orchestrator ;
- queue LAB ;
- JavaScript player ;
- styles globaux du LAB.

Les règles restaurées proviennent du CSS historique du benchmark validé avant la refonte LAB.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_CHORDS_UI_R2C.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\apply-chords-ui-r2c.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-chords-ui-r2c.ps1
```

Puis recharger la page CHORDS avec `Ctrl+F5`.
