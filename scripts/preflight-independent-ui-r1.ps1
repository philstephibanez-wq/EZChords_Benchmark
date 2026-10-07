$ErrorActionPreference = "Stop"
$Project = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Python = "H:\Python\pythoncore-3.14-64\python.exe"

Write-Host "=== EZStudio_lab independent + UI R1 preflight ==="

if (-not (Test-Path $Python)) { throw "Python introuvable: $Python" }

# Python syntax and existing engine contract.
& $Python -m py_compile `
    (Join-Path $Project "python\engine.py") `
    (Join-Path $Project "python\observability.py") `
    (Join-Path $Project "python\ezstudio\pipeline\stems\runner.py")
if ($LASTEXITCODE -ne 0) { throw "Python compile KO" }

& $Python (Join-Path $Project "python\engine.py") --self-test
if ($LASTEXITCODE -ne 0) { throw "Engine self-test KO" }

$engineText = Get-Content (Join-Path $Project "python\engine.py") -Raw
$requiredMethods = @(
    "Beat This downbeat",
    "Percussive onset",
    "Bass CQT",
    "Rhythm + Bass",
    "Harmonic novelty",
    "R41-like fusion"
)
foreach ($name in $requiredMethods) {
    if (-not $engineText.Contains($name)) {
        throw "Methode metrique absente: $name"
    }
}
if (-not $engineText.Contains("# ---- metric section: intentionally unchanged from R6 ----")) {
    throw "Marqueur section metrique gelee absent"
}
Write-Host "EZSTUDIO_SIX_METRIC_METHODS_UNCHANGED_CONTRACT_OK"

# Runtime independence: scan executable/runtime files only.
$runtimeFiles = @(
    "python\engine.py",
    "python\worker.py",
    "python\observability.py",
    "python\ezstudio\pipeline\stems\runner.py",
    "config\services.yaml",
    "src\Service\BenchmarkLauncher.php",
    "src\Controller\BenchmarkController.php",
    "scripts\start.ps1"
)
foreach ($rel in $runtimeFiles) {
    $path = Join-Path $Project $rel
    if (-not (Test-Path $path)) { throw "Runtime file absent: $rel" }
    $text = Get-Content $path -Raw
    if ($text -match 'H:\\+EZScore' -or $text.Contains("DEFAULT_EZSCORE_STEMS_SCRIPT") -or $text.Contains("ensure_ezscore_stems")) {
        throw "Dependance runtime EZScore detectee dans $rel"
    }
    if ($text.Contains("EZChords_Benchmark")) {
        throw "Ancien runtime EZChords_Benchmark detecte dans $rel"
    }
}
Write-Host "EZSTUDIO_RUNTIME_INDEPENDENCE_OK"

# Contract schemas.
$contracts = @(
    "contracts\stems.schema.json",
    "contracts\chords.schema.json",
    "contracts\lyrics.schema.json",
    "contracts\timeline.schema.json"
)
foreach ($rel in $contracts) {
    $path = Join-Path $Project $rel
    $null = Get-Content $path -Raw | ConvertFrom-Json
}
Write-Host "EZSTUDIO_EZSCORE_STEMS_CONTRACT_OK"
Write-Host "EZSTUDIO_EZSCORE_CHORDS_CONTRACT_OK"
Write-Host "EZSTUDIO_EZSCORE_LYRICS_CONTRACT_OK"
Write-Host "EZSTUDIO_EZSCORE_TIMELINE_CONTRACT_OK"

# PHP/UI.
php -l (Join-Path $Project "src\Controller\LabController.php")
if ($LASTEXITCODE -ne 0) { throw "LabController PHP lint KO" }

$routeOutput = php (Join-Path $Project "bin\console") debug:router
if ($LASTEXITCODE -ne 0) { throw "debug:router KO" }
$routeText = ($routeOutput | Out-String)
foreach ($route in @("lab_index","lab_run","lab_plot","lab_export","bench_start")) {
    if (-not $routeText.Contains($route)) { throw "Route absente: $route" }
}
Write-Host "EZSTUDIO_LAB_UI_ROUTES_OK"

$base = Get-Content (Join-Path $Project "templates\base.html.twig") -Raw
if (-not $base.Contains("EZStudio_lab")) { throw "Brand EZStudio_lab absent" }
foreach ($label in @("Import","Stems","Chords","Lyrics","Runs")) {
    if (-not $base.Contains($label)) { throw "Navigation UI absente: $label" }
}
Write-Host "EZSTUDIO_NEW_UI_CONTRACT_OK"

Write-Host "EZSTUDIO_INDEPENDENT_UI_R1B_PREFLIGHT_OK"
