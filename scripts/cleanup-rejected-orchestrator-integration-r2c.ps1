$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

Write-Host "=== EZStudio_lab R2C cleanup ==="

$remove = @(
    ".\python\ezstudio\jobs\stems_worker.py",
    ".\python\ezstudio\jobs\orchestrator_guard.py",
    ".\scripts\start-stems-worker.ps1",
    ".\scripts\status-stems-worker.ps1",
    ".\scripts\stop-stems-worker.ps1",
    ".\scripts\lab-job-store.php",
    ".\src\Controller\InternalAnalysisController.php",
    ".\analysis\worker_entrypoint.py",
    ".\scripts\install-orchestrator-token.ps1",
    ".\scripts\install-analysis-token-r2b.ps1"
)

foreach ($path in $remove) {
    if (Test-Path $path) {
        Remove-Item -LiteralPath $path -Force
        Write-Host "DELETED $path"
    } else {
        Write-Host "ABSENT  $path"
    }
}

# Remove the R2A auto-start block if present.
$startPath = Join-Path $Root "scripts\start.ps1"
if (Test-Path $startPath) {
    $text = Get-Content $startPath -Raw
    $marker = '$stemsWorkerStart = Join-Path $root "scripts\start-stems-worker.ps1"'
    if ($text.Contains($marker)) {
        $begin = $text.IndexOf($marker)
        $tail = 'if ($LASTEXITCODE -ne 0) { throw "STEMS worker startup failed" }'
        $end = $text.IndexOf($tail, $begin)
        if ($end -lt 0) {
            throw "Incomplete rejected R2A worker block in scripts\start.ps1"
        }
        $end = $end + $tail.Length
        while ($end -lt $text.Length -and ($text[$end] -eq "`r" -or $text[$end] -eq "`n")) {
            $end++
        }
        $text = $text.Substring(0, $begin) + $text.Substring($end)
        $enc = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($startPath, $text, $enc)
        Write-Host "REMOVED rejected R2A worker auto-start"
    }
}

Write-Host "EZSTUDIO_REJECTED_WORKERS_CLEANED_OK"
Write-Host "EZSTUDIO_ORCHESTRATOR_READONLY_OK"
