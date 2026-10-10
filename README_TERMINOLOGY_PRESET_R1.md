# EZStudio — TERMINOLOGY PRESET R1

Migration terminologique uniquement.

```text
Chaîne → Phase → Module → Engine / Model → Settings → Preset → Adapter
```

R1 introduit les noms canoniques dans le code avec aliases de compatibilité.
Aucun algorithme, seuil, moteur, modèle, taxonomie, consensus ou ordre d'exécution n'est modifié.

Restent volontairement inchangés pour le contrôle de non-régression :
- SQLite ;
- tables historiques `genome_*` ;
- clés JSON persistées historiques ;
- routes `/dna/*` ;
- schéma `ezstudio.gene-spec.v1` ;
- chemins legacy nécessaires aux imports.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_TERMINOLOGY_PRESET_R1.zip" -C H:\EZStudio_lab

powershell -ExecutionPolicy Bypass -File .\scripts\apply_terminology_preset_r1.ps1

H:\Python\pythoncore-3.14-64\python.exe .\scripts\test_terminology_preset_r1.py
php .\scripts\test_terminology_preset_r1.php

H:\Python\pythoncore-3.14-64\python.exe .\scripts\test_declarative_runtime_v1a.py
H:\Python\pythoncore-3.14-64\python.exe .\scripts\test_declarative_runtime_v1b.py
H:\Python\pythoncore-3.14-64\python.exe .\scripts\test_profile_r3b35c_contract.py
php .\scripts\test_profile_form_fr_r1e.php

php bin\console lint:container
php bin\console lint:twig templates
php bin\console cache:clear

git diff --check
git status --short
```

Après réussite : run PROFILE de référence puis contrôle CHORDS/N.
Le moteur déclaratif reste gelé jusqu'à validation de non-régression.
