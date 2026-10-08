# EZStudio_lab — STEMS -> CHORDS DNA R3B4A HOTFIX

## Défauts corrigés

1. `src/Service/LabJobStore.php`
   - parenthèse fermante manquante dans le comparateur `usort()`;
   - c'était la cause exacte du `PHP Parse error` ligne 178.

2. `tests/stems_chords_dna_r3b4_contract.php`
   - le test cherchait à tort le littéral `scientific_run_id` dans `StemsLabController.php`;
   - l'identifiant scientifique est transmis à `createStemsJob()` puis sérialisé par `LabJobStore`;
   - le test vérifie maintenant le binding ADN côté contrôleur et la persistance `scientific_run_id/lineage` côté store.
   - une assertion Twig trop fragile sur l'apostrophe a aussi été rendue robuste.

## Contrôles effectués avant livraison

- `php -l` sur tous les fichiers PHP du package R3B4 fusionné avec le hotfix ;
- exécution réelle du test statique `stems_chords_dna_r3b4_contract.php` sur l'arbre fusionné.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_STEMS_CHORDS_DNA_R3B4A_HOTFIX.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\apply-stems-chords-dna-r3b4.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-stems-chords-dna-r3b4.ps1
```
