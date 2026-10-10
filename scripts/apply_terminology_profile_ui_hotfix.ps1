$ErrorActionPreference = 'Stop'

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$profile = Join-Path $root 'templates\workbench\profile.html.twig'
$summary = Join-Path $root 'src\Service\ProfileFrenchSummary.php'

if (-not (Test-Path $profile)) { throw "Fichier introuvable: $profile" }
if (-not (Test-Path $summary)) { throw "Fichier introuvable: $summary" }

# PROFILE template — visible terminology only.
$text = [System.IO.File]::ReadAllText($profile)

$replacements = [ordered]@{
    'Région PROFILE du chromosome : caractérisation globale du master avant STEMS.' =
        'Phase PROFILE de la chaîne : caractérisation globale du master avant STEMS.'

    'Autres éléments sonores conservés dans l’ADN' =
        'Autres éléments sonores conservés dans le résultat d’analyse'

    'Le formulaire valide les conclusions principales ; l’ADN conserve les données scientifiques et les scores d’origine.' =
        'Le formulaire valide les conclusions principales ; le run conserve les données scientifiques et les scores d’origine.'

    "{{ subject.scope == 'gene' ? 'Gène' : 'Région' }}" =
        "{{ subject.scope == 'gene' ? 'Module' : 'Phase' }}"

    '<h2>Gènes PROFILE</h2>' =
        '<h2>Modules PROFILE</h2>'

    'gène(s) OK' =
        'module(s) OK'

    '<th>Gène</th><th>Famille</th>' =
        '<th>Module</th><th>Famille</th>'

    '<th>Gène</th><th>Tonalité</th>' =
        '<th>Module</th><th>Tonalité</th>'

    '>Run ADN PROFILE</a>' =
        '>Run PROFILE</a>'
}

foreach ($key in $replacements.Keys) {
    $text = $text.Replace($key, $replacements[$key])
}

[System.IO.File]::WriteAllText(
    $profile,
    $text,
    [System.Text.UTF8Encoding]::new($false)
)

# PROFILE French summary — visible terminology only.
$text = [System.IO.File]::ReadAllText($summary)
$text = $text.Replace(
    'Résumé déterministe dérivé de l’ADN.',
    'Résumé déterministe dérivé du run PROFILE.'
)
[System.IO.File]::WriteAllText(
    $summary,
    $text,
    [System.Text.UTF8Encoding]::new($false)
)

Write-Host 'TERMINOLOGY_PROFILE_UI_HOTFIX_APPLIED' -ForegroundColor Green
Write-Host 'PROFILE visible terminology updated'
Write-Host 'No logic, schema, route or scientific setting modified'
