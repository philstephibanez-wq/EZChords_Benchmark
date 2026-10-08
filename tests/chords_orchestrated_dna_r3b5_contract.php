<?php
declare(strict_types=1);

$root=dirname(__DIR__);
$db=file_get_contents($root.'/src/Service/Database.php');
$desktop=file_get_contents($root.'/src/Controller/AnalysisDesktopController.php');
$exec=file_get_contents($root.'/src/Service/ChordsDnaExecutionService.php');
$controller=file_get_contents($root.'/src/Controller/ChordsExperimentController.php');
$twig=file_get_contents($root.'/templates/lab/chords_experiment.html.twig');

foreach ([
    'queueScientificChordsJob',
    "'chords_scientific'",
    "'selection_request' =>",
    "'scientific_run_id' =>",
] as $needle) {
    if (!str_contains($db,$needle)) throw new RuntimeException('db_missing:'.$needle);
}
foreach ([
    'ChordsDnaExecutionService',
    'progressFromJob',
    'completeFromJob',
    'failFromJob',
] as $needle) {
    if (!str_contains($desktop,$needle)) throw new RuntimeException('desktop_missing:'.$needle);
}
foreach ([
    'benchmark_run',
    'analysis_job',
    'queueScientificChordsJob',
    'scientific_manifest',
    'chords_result',
] as $needle) {
    if (!str_contains($exec,$needle)) throw new RuntimeException('execution_missing:'.$needle);
}
if (!str_contains($controller,'$execution->queue')) {
    throw new RuntimeException('controller_does_not_queue');
}
if (!str_contains($twig,'Lancer l’analyse CHORDS versionnée')) {
    throw new RuntimeException('twig_launch_button_missing');
}
echo "EZSTUDIO_CHORDS_ORCHESTRATED_DNA_R3B5_PHP_CONTRACT_OK\n";
