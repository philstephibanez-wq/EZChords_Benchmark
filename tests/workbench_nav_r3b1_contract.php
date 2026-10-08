<?php
declare(strict_types=1);

$root=dirname(__DIR__);
$base=file_get_contents($root.'/templates/base.html.twig');
$controller=file_get_contents($root.'/src/Controller/WorkbenchController.php');
$catalog=file_get_contents($root.'/src/Service/WorkbenchCatalog.php');
$home=file_get_contents($root.'/templates/workbench/home.html.twig');

foreach ([
  "path('workbench_home')",
  "path('workbench_import'",
  "path('workbench_stems'",
  "path('workbench_chords'",
  "path('workbench_lyrics'",
  "path('workbench_runs'",
  "['workbench_chords','bench_view']",
  "['workbench_runs','lab_run']",
] as $needle) {
    if (!str_contains($base,$needle)) throw new RuntimeException('base_missing:'.$needle);
}

if (str_contains($base,'EZSTUDIO_NAV_ACTIVE_R3A3_JS')) {
    throw new RuntimeException('obsolete_r3a3_js_still_present');
}

foreach ([
  "#[Route('/home', name: 'workbench_home'",
  "#[Route('/workbench/chords', name: 'workbench_chords'",
  "generateUrl('bench_view'",
  "#[Route('/workbench/runs', name: 'workbench_runs'",
] as $needle) {
    if (!str_contains($controller,$needle)) throw new RuntimeException('controller_missing:'.$needle);
}

foreach ([
  "'stems_ready' => false",
  "'chords_ready' => false",
  "'latest_chords_run_id' => null",
  "no_chord_benchmark",
] as $needle) {
    if (!str_contains($catalog,$needle)) throw new RuntimeException('catalog_missing:'.$needle);
}

foreach ([
  'Chansons analysées',
  'song.stems_ready',
  'song.chords_ready',
  "path('bench_view',{id:song.latest_chords_run_id})",
  "path('lab_run',{id:song.latest_run_id})",
] as $needle) {
    if (!str_contains($home,$needle)) throw new RuntimeException('home_missing:'.$needle);
}

echo "EZSTUDIO_WORKBENCH_NAV_R3B1_CONTRACT_OK\n";
