$ErrorActionPreference = 'Stop'

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$path = Join-Path $root 'scripts\test_declarative_runtime_v1b.py'

if (-not (Test-Path $path)) {
    throw "Test V1B introuvable: $path"
}

$text = [System.IO.File]::ReadAllText($path)

if ($text -notmatch 'assert "load_gene_spec" in wrapper_text') {
    if ($text -match 'assert "load_module_config" in wrapper_text') {
        Write-Host 'TERMINOLOGY_PRESET_R1_TESTFIX_ALREADY_APPLIED' -ForegroundColor Yellow
        exit 0
    }
    throw 'Assertion V1B attendue introuvable; aucun fichier modifie.'
}

$text = $text.Replace(
    'assert "load_gene_spec" in wrapper_text',
    'assert "load_module_config" in wrapper_text'
)

[System.IO.File]::WriteAllText(
    $path,
    $text,
    [System.Text.UTF8Encoding]::new($false)
)

Write-Host 'TERMINOLOGY_PRESET_R1_TESTFIX_APPLIED' -ForegroundColor Green
Write-Host 'V1B contract now checks canonical load_module_config name'
Write-Host 'No scientific/runtime code modified'
