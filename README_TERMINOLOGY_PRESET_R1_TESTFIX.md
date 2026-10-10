# EZStudio — TERMINOLOGY PRESET R1 TESTFIX

Correction purement contractuelle.

Le test V1B vérifiait encore le symbole legacy :

`load_gene_spec`

Après TERMINOLOGY PRESET R1, le wrapper utilise légitimement :

`load_module_config`

Le loader legacy reste disponible comme alias, mais le test doit vérifier le nom canonique.

Aucun fichier scientifique/runtime n'est modifié.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_TERMINOLOGY_PRESET_R1_TESTFIX.zip" -C H:\EZStudio_lab

powershell -ExecutionPolicy Bypass -File .\scripts\apply_terminology_preset_r1_testfix.ps1

H:\Python\pythoncore-3.14-64\python.exe .\scripts\test_declarative_runtime_v1b.py
H:\Python\pythoncore-3.14-64\python.exe .\scripts\test_terminology_preset_r1.py
H:\Python\pythoncore-3.14-64\python.exe .\scripts\test_profile_r3b35c_contract.py

git diff --check
git status --short
```

Résultat attendu :

`DECLARATIVE_RUNTIME_V1B_CONTRACT_OK`
