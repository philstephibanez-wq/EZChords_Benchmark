param([switch]$Yes)

$ErrorActionPreference = "Stop"

$Project = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$RuntimeRoot = "H:\temp\EZStudio_lab"
$Database = Join-Path $Project "data\benchmark.sqlite"
$PublicAudio = Join-Path $Project "public\benchmark-audio"
$Php = "H:\PHP\php-8.5-x64\php.exe"
$Python = "H:\Python\pythoncore-3.14-64\python.exe"

function Write-Utf8NoBom {
    param([string]$Path, [string]$Content)
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $enc)
}

function Remove-Tree {
    param([string]$Path)
    if (Test-Path $Path) {
        Remove-Item -LiteralPath $Path -Recurse -Force
        Write-Host "DELETED $Path"
    } else {
        Write-Host "ABSENT  $Path"
    }
}

function Remove-FileIfExists {
    param([string]$Path)
    if (Test-Path $Path) {
        Remove-Item -LiteralPath $Path -Force
        Write-Host "DELETED $Path"
    } else {
        Write-Host "ABSENT  $Path"
    }
}

Write-Host "=== EZStudio_lab RESET HISTORY R1E ==="
Write-Host "EZS_orchestrator is READ ONLY and is not touched."

if (-not $Yes) {
    $answer = Read-Host "Type RESET to continue"
    if ($answer.ToUpperInvariant() -ne "RESET") {
        Write-Host "RESET_CANCELLED"
        exit 2
    }
}

Remove-FileIfExists $Database
Remove-FileIfExists ($Database + "-wal")
Remove-FileIfExists ($Database + "-shm")
Remove-Tree $PublicAudio

foreach ($name in @(
    "stems",
    "observability",
    "exports",
    "jobs",
    "uploads",
    "work",
    "launcher",
    "worker"
)) {
    Remove-Tree (Join-Path $RuntimeRoot $name)
}

$mongoReset = @'
from pymongo import MongoClient
client = MongoClient("mongodb://127.0.0.1:27017", serverSelectionTimeoutMS=3000)
client.admin.command("ping")
client.drop_database("ezstudio_lab")
if "ezstudio_lab" in client.list_database_names():
    raise SystemExit("ezstudio_lab still exists")
print("EZSTUDIO_MONGO_DROP_OK")
'@

$mongoScript = Join-Path $Project "var\reset-history-mongo.py"
New-Item -ItemType Directory -Force -Path (Split-Path $mongoScript -Parent) | Out-Null
Write-Utf8NoBom -Path $mongoScript -Content $mongoReset
try {
    & $Python $mongoScript
    if ($LASTEXITCODE -ne 0) { throw "Mongo reset failed" }
} finally {
    Remove-Item $mongoScript -Force -ErrorAction SilentlyContinue
}

$projectLiteral = $Project.Replace('\', '\\').Replace("'", "\'")
$bootstrap = @"
<?php
`$project = '$projectLiteral';
require `$project . '/vendor/autoload.php';
`$db = new App\Service\Database(`$project . '/data/benchmark.sqlite');
`$db->pdo();
echo "EMPTY_DB_SCHEMA_OK\n";
"@

$tmp = Join-Path $Project "var\reset-history-bootstrap.php"
Write-Utf8NoBom -Path $tmp -Content $bootstrap
try {
    & $Php $tmp
    if ($LASTEXITCODE -ne 0) { throw "SQLite schema recreation failed" }
} finally {
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
}

$databaseForPhp = $Database.Replace('\', '/')
$check = @"
<?php
`$db = new PDO('sqlite:$databaseForPhp');
`$tables = ['songs','benchmark_runs','algorithm_results','judgements','run_reviews','algorithm_reviews','run_logs'];
foreach (`$tables as `$table) {
    if ((int)`$db->query("SELECT COUNT(*) FROM " . `$table)->fetchColumn() !== 0) {
        exit(3);
    }
}
echo "EZSTUDIO_SQLITE_HISTORY_EMPTY_OK\n";
"@

$checkPath = Join-Path $Project "var\reset-history-check.php"
Write-Utf8NoBom -Path $checkPath -Content $check
try {
    & $Php $checkPath
    if ($LASTEXITCODE -ne 0) { throw "SQLite empty validation failed" }
} finally {
    Remove-Item $checkPath -Force -ErrorAction SilentlyContinue
}

Write-Host "EZSTUDIO_RUNTIME_HISTORY_EMPTY_OK"
Write-Host "EZSTUDIO_ORCHESTRATOR_READONLY_OK"
Write-Host "EZSTUDIO_HISTORY_RESET_R1E_OK"
