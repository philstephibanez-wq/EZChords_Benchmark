<?php
declare(strict_types=1);

$base=file_get_contents(dirname(__DIR__).'/templates/base.html.twig');
if ($base === false) throw new RuntimeException('base_unreadable');

foreach ([
    'EZSTUDIO_NAV_ACTIVE_R3A3_CSS',
    'EZSTUDIO_NAV_ACTIVE_R3A3_JS',
    '.main-nav a.active',
    'aria-current',
    'hashchange',
    'IntersectionObserver',
    "['import','stems','chords','lyrics','runs']",
] as $needle) {
    if (!str_contains($base,$needle)) {
        throw new RuntimeException('nav_active_missing:'.$needle);
    }
}

echo "EZSTUDIO_NAV_ACTIVE_R3A3_CONTRACT_OK\n";
