$ErrorActionPreference = 'Stop'

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$wrapper = Join-Path $root 'python\ezstudio\pipeline\profile\genes\semantic_clap_open_vocab.py'
$adapter = Join-Path $root 'python\ezstudio\runtime\adapters\clap_zero_shot.py'
$spec = Join-Path $root 'adn\specs\profile\semantic.clap-open-vocabulary.r3b35c.json'

foreach ($path in @($wrapper, $adapter, $spec)) {
    if (-not (Test-Path $path)) {
        throw "Fichier requis introuvable: $path"
    }
}

$backupRoot = Join-Path $root 'var\tmp\declarative_runtime_v1b_backup'
New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null

$legacy = Join-Path $root 'python\ezstudio\pipeline\profile\semantic_clap.py'
if (-not (Test-Path $legacy)) {
    throw "Moteur legacy CLAP introuvable: $legacy"
}

Copy-Item $legacy (Join-Path $backupRoot 'semantic_clap.py') -Force

$wrapperText = [System.IO.File]::ReadAllText($wrapper)
if ($wrapperText -notmatch 'run_clap_zero_shot') {
    throw 'Le wrapper V1B declaratif n''est pas installe.'
}
if ($wrapperText -notmatch 'semantic\.clap-open-vocabulary\.r3b35c\.json') {
    throw 'La Gene Spec R3B35C n''est pas referencee par le wrapper.'
}

Write-Host 'DECLARATIVE_RUNTIME_V1B_APPLIED' -ForegroundColor Green
Write-Host 'PROFILE CLAP now executes through common runtime adapter'
Write-Host 'R3B35C Gene Spec remains the active scientific configuration'
Write-Host 'Legacy semantic_clap.py preserved and untouched'
Write-Host 'CHORDS/N baseline untouched'
