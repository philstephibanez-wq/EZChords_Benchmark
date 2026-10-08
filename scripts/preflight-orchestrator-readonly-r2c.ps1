$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Orchestrator = "H:\EZS_orchestrator"
$RuntimeConfig = Join-Path $Orchestrator "config\runtime.json"
$TargetContract = Join-Path $Orchestrator "contracts\target.py"
$Planner = Join-Path $Orchestrator "executor\planner.py"

if (-not (Test-Path $RuntimeConfig)) { throw "Orchestrator runtime config missing" }
if (-not (Test-Path $TargetContract)) { throw "Orchestrator target contract missing" }
if (-not (Test-Path $Planner)) { throw "Orchestrator planner missing" }

$config = Get-Content $RuntimeConfig -Raw | ConvertFrom-Json
$serverNames = @($config.servers.PSObject.Properties.Name)

if ($serverNames -contains "lab") {
    throw "Unexpected LAB target found in orchestrator. This R2C package assumes orchestrator was not patched."
}

if (-not ($serverNames -contains "dev") -or -not ($serverNames -contains "prod")) {
    throw "Unexpected orchestrator topology"
}

$targets = Get-Content $TargetContract -Raw
if ($targets -match 'LAB\s*=\s*"lab"') {
    throw "Unexpected Target.LAB found in orchestrator"
}

$plannerText = Get-Content $Planner -Raw
if (-not $plannerText.Contains("analysis_entrypoint")) {
    throw "Unexpected orchestrator planner contract"
}

Write-Host "EZS_ORCHESTRATOR_TARGETS_DEV_PROD_ONLY_OK"
Write-Host "EZS_ORCHESTRATOR_TARGET_OWNED_ENTRYPOINT_OK"
Write-Host "EZSTUDIO_ORCHESTRATOR_READONLY_R2C_PREFLIGHT_OK"
