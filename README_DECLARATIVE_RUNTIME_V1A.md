# EZStudio — Declarative Gene Runtime V1A

## Purpose

V1A establishes the common declarative runtime contract for all chromosome regions:

- PROFILE
- STEMS
- CHORDS/N
- LYRICS

It intentionally **does not modify any existing scientific runner**. This makes V1A a zero-regression foundation step.

## What is installed

- `python/ezstudio/runtime/gene_spec.py` — JSON Gene Spec loader + strict validation
- `python/ezstudio/runtime/engine_registry.py` — region-agnostic engine adapter registry
- `python/ezstudio/runtime/decision.py` — generic decision primitives
- `adn/specs/profile/semantic.clap-open-vocabulary.r3b35c.json` — declarative encoding of the current PROFILE CLAP DNA
- contract test

## Important

The PROFILE Gene Spec deliberately reproduces the current R3B35C CLAP taxonomy and top-k settings. It is a compatibility encoding, not an improvement.

CHORDS/N is not modified. It remains a protected scientific baseline.

## Apply / test

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_DECLARATIVE_RUNTIME_V1A.zip" -C H:\EZStudio_lab

powershell -ExecutionPolicy Bypass -File .\scripts\apply_declarative_runtime_v1a.ps1

H:\Python\pythoncore-3.14-64\python.exe .\scripts\test_declarative_runtime_v1a.py

git diff --check
git status --short
```

Expected:

```text
DECLARATIVE_RUNTIME_V1A_APPLIED
Common runtime installed
PROFILE R3B35C CLAP Gene Spec encoded
No existing scientific runner modified
CHORDS/N baseline untouched

DECLARATIVE_RUNTIME_V1A_CONTRACT_OK
Common runtime: profile/stems/chords/lyrics
PROFILE R3B35C CLAP Gene Spec encoded without changing execution
No scientific mutation in V1A
```

## Next step — V1B

After V1A passes locally, PROFILE CLAP is switched to execute through this runtime while keeping the R3B35C Gene Spec unchanged. The acceptance criterion is output equivalence before any R3B36 mutation.
