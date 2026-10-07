$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "=== EZChords Benchmark V7N.2 preflight ==="

$utf8 = New-Object System.Text.UTF8Encoding($false)
$enginePath = Join-Path $root "python\engine.py"
$viewPath = Join-Path $root "templates\benchmark\view.html.twig"
$controllerPath = Join-Path $root "src\Controller\BenchmarkController.php"

$engine = [System.IO.File]::ReadAllText($enginePath, $utf8)
$view = [System.IO.File]::ReadAllText($viewPath, $utf8)
$controller = [System.IO.File]::ReadAllText($controllerPath, $utf8)

if ($engine -notmatch 'NO_CHORD = "N"') { throw "V7N_INTERNAL_N_MISSING" }

# Search for an actual function definition, not a documentation/test string.
if ($engine -match '(?m)^\s*def\s+harmonic_silence_mask\s*\(') {
    throw "V7N_OLD_RMS_SILENCE_LOGIC_PRESENT"
}

if ($engine -notmatch "ismir2017") { throw "V7N_LV_CHORDIA_N_MISSING" }
if ($engine -notmatch "DEFAULT_EZSCORE_STEMS_SCRIPT") { throw "V7N_EZSCORE_STEMS_ADAPTER_MISSING" }
if ($engine -notmatch [regex]::Escape('H:\temp\EZChords_Benchmark\stems')) { throw "V7N_TEMP_STEMS_ROOT_MISSING" }
if ($engine -match [regex]::Escape('H:\EZScore\var\')) { throw "V7N_FORBIDDEN_EZSCORE_WRITE_PATH" }
if ($engine -notmatch '"read_only_ezscore": True') { throw "V7N_EZSCORE_READ_ONLY_CONTRACT_MISSING" }

$quarterRest = [char]::ConvertFromUtf32(0x1D13D)
$eighthRest = [char]::ConvertFromUtf32(0x1D13E)

if (-not $view.Contains($quarterRest)) { throw "V7N_QUARTER_REST_GLYPH_MISSING" }
if (-not $view.Contains($eighthRest)) { throw "V7N_EIGHTH_REST_GLYPH_MISSING" }
if ($controller -notmatch "no_chord_benchmark") { throw "V7N_CONTROLLER_DIAGNOSTIC_MISSING" }

& H:\Python\pythoncore-3.14-64\python.exe -m py_compile .\python\engine.py
if ($LASTEXITCODE -ne 0) { throw "V7N_PYTHON_COMPILE_FAILED" }

Write-Host "V7N_INTERNAL_N_OK"
Write-Host "V7N_OLD_RMS_SILENCE_REMOVED_OK"
Write-Host "V7N_NATIVE_LV_CHORDIA_N_OK"
Write-Host "V7N_EZSCORE_READ_ONLY_OK"
Write-Host "V7N_STEMS_TEMP_ONLY_OK"
Write-Host "V7N_REST_GLYPHS_OK"
Write-Host "V7N_PREFLIGHT_OK"
