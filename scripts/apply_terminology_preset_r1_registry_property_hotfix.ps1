$ErrorActionPreference = 'Stop'

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$src = Join-Path $root 'src'

$changed = 0
$files = Get-ChildItem $src -Recurse -Filter '*.php'

foreach ($file in $files) {
    $text = [System.IO.File]::ReadAllText($file.FullName)
    $original = $text

    # Canonical injected registry name.
    $text = $text.Replace('AnalysisRunRegistry $runs', 'AnalysisRunRegistry $runRegistry')

    # Canonical promoted property usages.
    # This is intentionally limited to object-property accesses produced by R1.
    $text = $text.Replace('$this->runs->', '$this->runRegistry->')

    if ($text -ne $original) {
        [System.IO.File]::WriteAllText(
            $file.FullName,
            $text,
            [System.Text.UTF8Encoding]::new($false)
        )
        $changed++
    }
}

# Harden R1 migration script for future re-application.
$apply = Join-Path $root 'scripts\apply_terminology_preset_r1.py'
if (Test-Path $apply) {
    $text = [System.IO.File]::ReadAllText($apply)
    $text = $text.Replace(
        'text = text.replace("$this->dna", "$this->runs")',
        'text = text.replace("$this->dna", "$this->runRegistry")'
    )
    $text = $text.Replace(
        'text = text.replace("AnalysisRunRegistry $dna", "AnalysisRunRegistry $runs")',
        'text = text.replace("AnalysisRunRegistry $dna", "AnalysisRunRegistry $runRegistry")'
    )
    [System.IO.File]::WriteAllText(
        $apply,
        $text,
        [System.Text.UTF8Encoding]::new($false)
    )
}

Write-Host 'TERMINOLOGY_PRESET_R1_REGISTRY_PROPERTY_HOTFIX_APPLIED' -ForegroundColor Green
Write-Host "PHP files changed: $changed"
Write-Host 'All AnalysisRunRegistry object-property accesses now use $this->runRegistry'
Write-Host 'No scientific logic modified'
