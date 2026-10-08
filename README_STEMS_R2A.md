# EZStudio_lab — STEMS R2A

**Aucun fichier d'EZS_orchestrator n'est modifié.**

EZStudio_lab importe uniquement le `ExecutionSingleton` existant depuis :

```text
H:\EZS_orchestrator\runtime_guard\singleton.py
```

Ainsi les jobs STEMS d'EZStudio_lab respectent le même mutex GPU machine que les jobs EZScore gérés par l'orchestrator.

```text
EZStudio UI -> queue locale -> worker EZStudio -> EZS_orchestrator ExecutionSingleton -> GPU -> STEMS
```

Installation :

```powershell
cd H:\EZStudio_lab
tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_STEMS_R2A_ORCHESTRATOR_GUARD.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\apply-stems-r2a.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-stems-r2a.ps1
```

Le précédent `EZS_orchestrator_LAB_TARGET_R1.zip` est rejeté et ne doit pas être appliqué.
