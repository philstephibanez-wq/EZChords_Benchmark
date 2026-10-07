$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "=== EZChords Benchmark V7N.4b Windows async preflight ==="

$utf8 = New-Object System.Text.UTF8Encoding($false)
$launcher = [System.IO.File]::ReadAllText((Join-Path $root "src\Service\BenchmarkLauncher.php"), $utf8)
$starter = [System.IO.File]::ReadAllText((Join-Path $root "scripts\start-benchmark-worker.ps1"), $utf8)

if ($launcher -match '\bpassthru\s*\(') { throw "V7N4B_SYNCHRONOUS_PASSTHRU_PRESENT" }
if ($launcher -match 'start "" /B') { throw "V7N4B_OLD_CMD_START_PRESENT" }
if ($launcher -notmatch 'start-benchmark-worker\.ps1') { throw "V7N4B_STARTER_NOT_REFERENCED" }
if ($starter -notmatch 'Start-Process') { throw "V7N4B_START_PROCESS_MISSING" }
if ($starter -match '-Wait') { throw "V7N4B_START_PROCESS_MUST_NOT_WAIT" }
if ($launcher -match 'H:\\EZScore\\var\\') { throw "V7N4B_FORBIDDEN_EZSCORE_WRITE_PATH" }

& php -l .\src\Service\BenchmarkLauncher.php
if ($LASTEXITCODE -ne 0) { throw "V7N4B_LAUNCHER_PHP_SYNTAX_FAILED" }

# Parse the PowerShell script without executing it.
$tokens = $null
$errors = $null
[System.Management.Automation.Language.Parser]::ParseFile(
    (Join-Path $root "scripts\start-benchmark-worker.ps1"),
    [ref]$tokens,
    [ref]$errors
) | Out-Null

if ($errors.Count -gt 0) {
    $errors | ForEach-Object { Write-Host $_.Message }
    throw "V7N4B_STARTER_POWERSHELL_SYNTAX_FAILED"
}

Write-Host "V7N4B_START_PROCESS_OK"
Write-Host "V7N4B_NO_CMD_START_OK"
Write-Host "V7N4B_NO_WAIT_OK"
Write-Host "V7N4B_EZSCORE_UNTOUCHED_OK"
Write-Host "V7N4B_PREFLIGHT_OK"
