# EZStudio PROFILE — formulaire français R1e

R1e abandonne les micro-patchs.

Le script remplace intégralement le bloc Twig compris entre :

```twig
{% if selected_profile_run.state == 'done' and profile_validation_subjects %}
```

et :

```twig
{% set pv = selected_profile_run.diagnostics.profile_view ?? {} %}
```

Si l'une des deux bornes manque, le script s'arrête **avant toute écriture**.

Aucun PHP ni Python n'est modifié.

## Installation

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_PROFILE_FORM_FR_R1e_BLOCK_REPLACE.zip" -C H:\EZStudio_lab

powershell -ExecutionPolicy Bypass -File .\scripts\apply_profile_form_fr_r1e.ps1

php .\scripts\test_profile_form_fr_r1e.php

php bin\console lint:twig templates\workbench\profile.html.twig

git diff --check
git status --short
```

Attendu :

```text
PROFILE_FORM_FR_R1E_APPLIED
Bloc Validation humaine remplace integralement
Aucun PHP/Python modifie
Scientific revision unchanged: R3B35C

PROFILE_FORM_FR_R1E_CONTRACT_OK
Validation block replacement verified
Scientific revision unchanged: R3B35C
```
