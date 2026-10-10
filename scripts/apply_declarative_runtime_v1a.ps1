$ErrorActionPreference = 'Stop'
$Repo = Split-Path -Parent $PSScriptRoot

$Required = @(
  'python\ezstudio\runtime\__init__.py',
  'python\ezstudio\runtime\gene_spec.py',
  'python\ezstudio\runtime\engine_registry.py',
  'python\ezstudio\runtime\decision.py',
  'python\ezstudio\runtime\adapters\__init__.py',
  'adn\specs\profile\semantic.clap-open-vocabulary.r3b35c.json',
  'scripts\test_declarative_runtime_v1a.py'
)

foreach ($relative in $Required) {
    $path = Join-Path $Repo $relative
    if (-not (Test-Path $path)) {
        throw "Fichier runtime manquant: $path"
    }
}

# This installer intentionally does not edit any existing scientific runner.
# V1A establishes the common engine contract and encodes the current PROFILE DNA.
Write-Host 'DECLARATIVE_RUNTIME_V1A_APPLIED'
Write-Host 'Common runtime installed'
Write-Host 'PROFILE R3B35C CLAP Gene Spec encoded'
Write-Host 'No existing scientific runner modified'
Write-Host 'CHORDS/N baseline untouched'
