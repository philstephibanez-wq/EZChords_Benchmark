<?php
declare(strict_types=1);

$root = dirname(__DIR__);
$profile = file_get_contents($root.'/templates/workbench/profile.html.twig');
$summary = file_get_contents($root.'/src/Service/ProfileFrenchSummary.php');

if ($profile === false || $summary === false) {
    throw new RuntimeException('profile_ui_source_unreadable');
}

$required = [
    'Phase PROFILE de la chaîne : caractérisation globale du master avant STEMS.',
    "subject.scope == 'gene' ? 'Module' : 'Phase'",
    '<h2>Modules PROFILE</h2>',
    'module(s) OK',
    '<th>Module</th><th>Famille</th>',
    '<th>Module</th><th>Tonalité</th>',
    '>Run PROFILE</a>',
    'résultat d’analyse',
];

foreach ($required as $needle) {
    if (!str_contains($profile, $needle)) {
        throw new RuntimeException('profile_ui_missing:'.$needle);
    }
}

$forbidden = [
    'Région PROFILE du chromosome',
    '<h2>Gènes PROFILE</h2>',
    '>Run ADN PROFILE</a>',
    'conservés dans l’ADN',
];

foreach ($forbidden as $needle) {
    if (str_contains($profile, $needle)) {
        throw new RuntimeException('profile_ui_legacy_visible:'.$needle);
    }
}

if (!str_contains($summary, 'Résumé déterministe dérivé du run PROFILE.')) {
    throw new RuntimeException('profile_summary_terminology_missing');
}
if (str_contains($summary, 'Résumé déterministe dérivé de l’ADN.')) {
    throw new RuntimeException('profile_summary_legacy_adn');
}

echo "TERMINOLOGY_PROFILE_UI_HOTFIX_CONTRACT_OK\n";
echo "PROFILE visible vocabulary is Phase / Module / Run\n";
