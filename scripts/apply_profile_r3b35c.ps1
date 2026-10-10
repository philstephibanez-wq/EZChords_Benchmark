$ErrorActionPreference = 'Stop'

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$registryPath = Join-Path $root 'python\ezstudio\pipeline\profile\gene_registry.py'
$runnerPath = Join-Path $root 'python\ezstudio\pipeline\profile\runner.py'
$canonicalPath = Join-Path $root 'python\ezstudio\pipeline\profile\canonical_profile.py'

foreach ($path in @($registryPath, $runnerPath, $canonicalPath)) {
    if (-not (Test-Path $path)) {
        throw "Fichier requis introuvable: $path"
    }
}

function Write-Utf8NoBom([string]$Path, [string]$Content) {
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $utf8)
}

$registry = [System.IO.File]::ReadAllText($registryPath)
$runner = [System.IO.File]::ReadAllText($runnerPath)

# 1) Import canonique, idempotent.
if ($registry -notmatch 'from canonical_profile import build_genre_hierarchy, build_vocal_profile') {
    $anchor = 'from gene import GeneContext, GeneSpec, run_gene'
    if (-not $registry.Contains($anchor)) {
        throw 'Ancre gene_registry import introuvable.'
    }
    $registry = $registry.Replace(
        $anchor,
        $anchor + "`r`nfrom canonical_profile import build_genre_hierarchy, build_vocal_profile"
    )
}

# 2) Révision génomique. On accepte R3B31..R3B35B comme source locale.
$registry = [regex]::Replace(
    $registry,
    '"pipeline_revision"\s*:\s*"profile-r3b[^"]+"',
    '"pipeline_revision": "profile-r3b35c-canonical-genre-vocals"',
    1
)

# 3) Projection parallèle : ne supprime ni semantic, ni instrumentation, ni l'ancien choirs.
if ($registry -notmatch '"genre_hierarchy"\s*:\s*build_genre_hierarchy\(semantic\)') {
    $needle = '"semantic": semantic,'
    $replacement = @'
"semantic": semantic,
        "genre_hierarchy": build_genre_hierarchy(semantic),
        "vocal_profile": build_vocal_profile(semantic),
'@
    $idx = $registry.LastIndexOf($needle)
    if ($idx -lt 0) {
        throw 'Ancre consensus semantic introuvable.'
    }
    $registry = $registry.Substring(0, $idx) + $replacement + $registry.Substring($idx + $needle.Length)
}

# 4) Vue PROFILE : exposer les nouveaux contrats sans retirer les anciens.
if ($runner -notmatch '"genre_hierarchy"\s*:\s*consensus\.get\("genre_hierarchy"\)') {
    $needle = '"tonal": consensus.get("tonal") or {},'
    if (-not $runner.Contains($needle)) {
        throw 'Ancre _profile_view tonal introuvable.'
    }
    $runner = $runner.Replace(
        $needle,
        $needle + "`r`n        `"genre_hierarchy`": consensus.get(`"genre_hierarchy`") or {},`r`n        `"vocal_profile`": consensus.get(`"vocal_profile`") or {},"
    )
}

# 5) Marqueurs de révision. Pas de modification des moteurs/gènes.
if ($runner -notmatch 'R3B35C_CANONICAL_PROFILE') {
    $constAnchor = 'R3B31_GENOMIC_EVOLUTION = True'
    if ($runner.Contains($constAnchor)) {
        $runner = $runner.Replace($constAnchor, $constAnchor + "`r`nR3B35C_CANONICAL_PROFILE = True")
    } else {
        $schemaAnchor = 'SCHEMA = "ezstudio.profile.v1"'
        if (-not $runner.Contains($schemaAnchor)) {
            throw 'Ancre constante runner introuvable.'
        }
        $runner = $runner.Replace($schemaAnchor, $schemaAnchor + "`r`nR3B35C_CANONICAL_PROFILE = True")
    }
}

$runner = [regex]::Replace(
    $runner,
    '"profile_architecture"\s*:\s*"genes-r3b[^"]+"',
    '"profile_architecture": "genes-r3b35c-canonical-contract"',
    1
)
$runner = [regex]::Replace(
    $runner,
    'PROFILE: écriture ADN R3B[0-9A-Z]+',
    'PROFILE: écriture ADN R3B35C',
    1
)

Write-Utf8NoBom $registryPath $registry
Write-Utf8NoBom $runnerPath $runner

Write-Host 'R3B35C applique.' -ForegroundColor Green
Write-Host 'Aucun moteur CLAP/PANNs/PaSST/MERT/Madmom n''a ete modifie.'
Write-Host 'Ancien consensus choirs conserve pour compatibilite; vocal_profile devient le contrat canonique.'
