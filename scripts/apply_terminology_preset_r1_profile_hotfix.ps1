$ErrorActionPreference = 'Stop'

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$targets = Get-ChildItem (Join-Path $root 'src') -Recurse -Filter '*.php'
$changed = 0

foreach ($file in $targets) {
    $text = [System.IO.File]::ReadAllText($file.FullName)
    $original = $text

    # Canonical service variable. Avoid collision with local $runs arrays.
    $text = $text.Replace('AnalysisRunRegistry $runs', 'AnalysisRunRegistry $runRegistry')
    $text = $text.Replace('$runs->', '$runRegistry->')

    if ($text -ne $original) {
        [System.IO.File]::WriteAllText(
            $file.FullName,
            $text,
            [System.Text.UTF8Encoding]::new($false)
        )
        $changed++
    }
}

# Harden the original R1 migration script so re-applying it cannot recreate
# the $runs service/local-array collision.
$apply = Join-Path $root 'scripts\apply_terminology_preset_r1.py'
if (Test-Path $apply) {
    $text = [System.IO.File]::ReadAllText($apply)
    $text = $text.Replace(
        'text = text.replace("AnalysisRunRegistry $dna", "AnalysisRunRegistry $runs")',
        'text = text.replace("AnalysisRunRegistry $dna", "AnalysisRunRegistry $runRegistry")'
    )
    $text = $text.Replace(
        'text = text.replace("$this->dna", "$this->runs")',
        'text = text.replace("$this->dna", "$this->runRegistry")'
    )
    $text = $text.Replace(
        'text = text.replace("$dna->", "$runs->")',
        'text = text.replace("$dna->", "$runRegistry->")'
    )
    [System.IO.File]::WriteAllText(
        $apply,
        $text,
        [System.Text.UTF8Encoding]::new($false)
    )
}

Write-Host 'TERMINOLOGY_PRESET_R1_PROFILE_HOTFIX_APPLIED' -ForegroundColor Green
Write-Host "PHP files changed: $changed"
Write-Host 'AnalysisRunRegistry variable is now $runRegistry'
Write-Host 'No scientific logic modified'
