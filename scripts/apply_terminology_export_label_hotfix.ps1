$ErrorActionPreference = 'Stop'

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$targets = @()
$targets += Get-ChildItem (Join-Path $root 'templates') -Recurse -File -ErrorAction SilentlyContinue
$targets += Get-ChildItem (Join-Path $root 'src') -Recurse -File -ErrorAction SilentlyContinue

$changed = 0
foreach ($file in $targets) {
    $text = [System.IO.File]::ReadAllText($file.FullName)
    if ($text.Contains('ZIP ADN')) {
        $text = $text.Replace('ZIP ADN', 'Exporter les Presets')
        [System.IO.File]::WriteAllText(
            $file.FullName,
            $text,
            [System.Text.UTF8Encoding]::new($false)
        )
        Write-Host "updated: $($file.FullName)"
        $changed++
    }
}

if ($changed -eq 0) {
    throw 'Libelle "ZIP ADN" introuvable; aucun fichier modifie.'
}

Write-Host 'TERMINOLOGY_EXPORT_LABEL_HOTFIX_APPLIED' -ForegroundColor Green
Write-Host "Files changed: $changed"
Write-Host 'Visible label: Exporter les Presets'
Write-Host 'Serialized export schema intentionally unchanged in R1'
