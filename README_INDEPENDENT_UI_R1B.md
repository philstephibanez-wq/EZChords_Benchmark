# EZStudio_lab — Independent Application + New UI R1B

R1B remplace R1/R1a. Il est conçu pour trois états d'entrée : dépôt propre, application R1 interrompue, état déjà migré.

Le défaut R1 venait d'une hypothèse incorrecte sur l'échappement du chemin PHP `H:\\temp\\EZChords_Benchmark\\stems`. R1B ne matche plus la ligne PHP complète : il migre l'identité applicative puis valide l'état final.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_INDEPENDENT_UI_R1B.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\apply-independent-ui-r1.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-independent-ui-r1.ps1
```

## Preflight attendu

La fin doit contenir :

```text
EZSTUDIO_SIX_METRIC_METHODS_UNCHANGED_CONTRACT_OK
EZSTUDIO_RUNTIME_INDEPENDENCE_OK
EZSTUDIO_EZSCORE_STEMS_CONTRACT_OK
EZSTUDIO_EZSCORE_CHORDS_CONTRACT_OK
EZSTUDIO_EZSCORE_LYRICS_CONTRACT_OK
EZSTUDIO_EZSCORE_TIMELINE_CONTRACT_OK
EZSTUDIO_LAB_UI_ROUTES_OK
EZSTUDIO_NEW_UI_CONTRACT_OK
EZSTUDIO_INDEPENDENT_UI_R1B_PREFLIGHT_OK
```

## Tests inclus

`python scripts/test-migration-r1b.py` vérifie :

- migration depuis le baseline historique ;
- réapplication idempotente ;
- reprise après migration partielle avec le chemin PHP à doubles backslashes ;
- lint PHP des fichiers migrés de fixture.

Le package conserve aussi l'UI, les contrats STEMS/CHORDS/LYRICS/TIMELINE et le pipeline STEMS autonome du R1.
