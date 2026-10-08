# EZStudio_lab — WORKBENCH R3A1 HOTFIX

Correctif du script de migration R3A.

Cause exacte :
`Path.write_text(..., newline="\\n")` recevait les deux caractères `\` + `n`
au lieu d'un vrai saut de ligne LF, ce que Python 3.14 refuse avec :

`ValueError: illegal newline value: \n`

R3A1 remplace cette valeur par un vrai `newline="\n"` et ajoute un test
spécifique avant migration.

Aucun fichier de production n'a été modifié par l'échec R3A initial avant
l'exception.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_WORKBENCH_R3A1_HOTFIX.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\apply-workbench-r3a1-hotfix.ps1

powershell -ExecutionPolicy Bypass -File .\scripts\preflight-workbench-r3a.ps1
```
