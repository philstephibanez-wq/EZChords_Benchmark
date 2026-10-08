$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$EnvPath = Join-Path $Root ".env.local"
$Key = "EZSTUDIO_ANALYSIS_WORKER_TOKEN"

$text = ""
if (Test-Path -LiteralPath $EnvPath) {
    $text = [System.IO.File]::ReadAllText($EnvPath)
}

$match = [regex]::Match(
    $text,
    "(?m)^\s*EZSTUDIO_ANALYSIS_WORKER_TOKEN\s*=\s*(.+?)\s*$"
)

if ($match.Success) {
    $current = $match.Groups[1].Value.Trim().Trim('"').Trim("'")
    if ($current.Length -ge 32) {
        Write-Host "EZSTUDIO_ANALYSIS_WORKER_TOKEN_ALREADY_CONFIGURED"
        exit 0
    }
}

$bytes = New-Object byte[] 48
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try {
    $rng.GetBytes($bytes)
} finally {
    $rng.Dispose()
}
$token = [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+','-').Replace('/','_')
$line = "$Key=$token"

if ($match.Success) {
    $text = [regex]::Replace(
        $text,
        "(?m)^\s*EZSTUDIO_ANALYSIS_WORKER_TOKEN\s*=.*$",
        $line,
        1
    )
} else {
    if ($text.Length -gt 0 -and -not $text.EndsWith("`n")) {
        $text += "`r`n"
    }
    $text += $line + "`r`n"
}

$enc = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($EnvPath, $text, $enc)

Write-Host "EZSTUDIO_ANALYSIS_WORKER_TOKEN_CONFIGURED"
