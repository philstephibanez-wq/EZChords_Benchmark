<?php
declare(strict_types=1);

$root=dirname(__DIR__);
$db=file_get_contents($root.'/src/Service/Database.php');
$controller=file_get_contents($root.'/src/Controller/LabController.php');
$template=file_get_contents($root.'/templates/lab/index.html.twig');

foreach ([
    'public function allSongs(): array',
    'public function song(int $id): ?array',
    'public function runsForSong(int $songId): array',
    'public function latestRunForSong(int $songId): ?array',
] as $needle) {
    if (!str_contains($db, $needle)) throw new RuntimeException('database_contract_missing:'.$needle);
}

foreach ([
    'Request $request, Database $db',
    "\$request->query->get('song')",
    "'songs' => \$songs",
    "'selected_song' => \$selectedSong",
] as $needle) {
    if (!str_contains($controller, $needle)) throw new RuntimeException('controller_contract_missing:'.$needle);
}

foreach ([
    '<h2>IMPORT</h2>',
    '<h2>Chansons</h2>',
    "path('lab_index', {song:song.id})",
    '<h2>STEMS</h2>',
    '<h2>CHORDS</h2>',
    '<h2>LYRICS</h2>',
    'Historique complet',
    'Résultats · Diagnostics · Comparaisons · Logs · Artefacts',
] as $needle) {
    if (!str_contains($template, $needle)) throw new RuntimeException('template_contract_missing:'.$needle);
}

foreach (['Mettre en queue','Queue EZStudio_lab','Orchestrator guard'] as $forbidden) {
    if (str_contains($template, $forbidden)) throw new RuntimeException('forbidden_lab_ui_vocabulary:'.$forbidden);
}

echo "EZSTUDIO_WORKBENCH_R3A_CONTRACT_OK\n";
