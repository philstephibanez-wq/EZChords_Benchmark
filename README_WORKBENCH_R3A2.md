# EZStudio_lab — WORKBENCH R3A2 FULL

R3A2 remplace les patchs R3A/R3A1 défaillants.

Cause R3A1 :
le script dépendait encore d'un littéral exact dans `Database.php`.
Le LAB local ayant évolué, cet ancrage n'existait plus.

R3A2 change la méthode :

- aucune dépendance à `public function allRuns(): array` comme ancre ;
- injection des nouvelles méthodes juste avant la fermeture finale de la classe ;
- remplacement du contrôleur par motif structurel `Route('/') -> prochaine Route('/lab/run/...')` ;
- migration idempotente ;
- tests synthétiques avant toute modification des fichiers applicatifs ;
- variantes LF / CRLF et différences d'indentation couvertes.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_WORKBENCH_R3A2_FULL.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\apply-workbench-r3a2.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-workbench-r3a2.ps1
```

Ne pas relancer R3A ni R3A1.
