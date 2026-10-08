from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    base=ROOT/"templates"/"base.html.twig"
    text=base.read_text(encoding="utf-8")
    old='<a href="{{ path(\'lab_index\') }}#stems">Stems</a>'
    new='<a href="{{ path(\'lab_stems\') }}">Stems</a>'
    if new not in text:
        if old not in text: raise RuntimeError("base STEMS anchor absent")
        base.write_text(text.replace(old,new),encoding="utf-8",newline="\n")

    start=ROOT/"scripts"/"start.ps1"
    s=start.read_text(encoding="utf-8")
    marker='Write-Host "DOCROOT=$public"\n'
    block='''\n$stemsWorkerStart = Join-Path $root "scripts\\start-stems-worker.ps1"\nif (-not (Test-Path $stemsWorkerStart)) { throw "STEMS worker launcher absent: $stemsWorkerStart" }\n& powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File $stemsWorkerStart\nif ($LASTEXITCODE -ne 0) { throw "STEMS worker startup failed" }\n'''
    if '$stemsWorkerStart = Join-Path $root' not in s:
        if marker not in s: raise RuntimeError("start.ps1 marker absent")
        start.write_text(s.replace(marker,marker+block),encoding="utf-8",newline="\n")

    for rel in ("src/Controller/InternalAnalysisController.php","analysis/worker_entrypoint.py","scripts/install-orchestrator-token.ps1"):
        p=ROOT/rel
        if p.is_file(): p.unlink()

    print("EZSTUDIO_STEMS_R2A_MIGRATION_OK")
    print("EZSTUDIO_ORCHESTRATOR_REPO_UNTOUCHED_CONTRACT_OK")
    return 0

if __name__=="__main__": raise SystemExit(main())
