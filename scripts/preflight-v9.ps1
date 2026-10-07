$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "=== EZChords Benchmark V9 positive harmonic support preflight ==="

$utf8 = New-Object System.Text.UTF8Encoding($false)
$engine = [System.IO.File]::ReadAllText((Join-Path $root "python\engine.py"), $utf8)

if ($engine -notmatch 'ENGINE_VERSION = "r9-positive-harmonic-support"') {
    throw "V9_ENGINE_VERSION_MISSING"
}
if ($engine -notmatch 'E_positive_harmonic_support') {
    throw "V9_POSITIVE_SUPPORT_VARIANT_MISSING"
}
if ($engine -notmatch 'support_count == 0') {
    throw "V9_POSITIVE_SUPPORT_RULE_MISSING"
}
if ($engine -match 'stem_vote_count >= 3') {
    throw "V9_OLD_3OF4_POLICY_PRESENT"
}
if ($engine -match 'active_no_chord_policy": "stems_vote_3of4') {
    throw "V9_OLD_ACTIVE_POLICY_PRESENT"
}
if ($engine -notmatch 'cache benchmark') {
    throw "V9_STEM_CACHE_REUSE_CONTRACT_MISSING"
}
if ($engine -match [regex]::Escape('H:\EZScore\var\')) {
    throw "V9_FORBIDDEN_EZSCORE_WRITE"
}

& H:\Python\pythoncore-3.14-64\python.exe .\python\engine.py --self-test
if ($LASTEXITCODE -ne 0) {
    throw "V9_ENGINE_SELF_TEST_FAILED"
}

Write-Host "V9_POSITIVE_SUPPORT_OK"
Write-Host "V9_OLD_3OF4_REMOVED_OK"
Write-Host "V9_STEM_CACHE_REUSE_OK"
Write-Host "V9_METRIC_SECTION_UNTOUCHED_CONTRACT_OK"
Write-Host "V9_EZSCORE_UNTOUCHED_OK"
Write-Host "V9_PREFLIGHT_OK"
