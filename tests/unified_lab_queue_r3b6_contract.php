<?php
declare(strict_types=1);

$root = dirname(__DIR__);
$db = file_get_contents($root.'/src/Service/Database.php');
$controller = file_get_contents($root.'/src/Controller/StemsLabController.php');
$desktop = file_get_contents($root.'/src/Controller/AnalysisDesktopController.php');
$service = file_get_contents($root.'/src/Service/StemsDnaExecutionService.php');
$entry = file_get_contents($root.'/analysis/worker_entrypoint.py');

foreach ([
    'scientific_run_id INTEGER',
    'song_id INTEGER NOT NULL',
    'source_path TEXT NOT NULL',
    'queueScientificStemsJob',
    'analysisJobsForSongKind',
] as $needle) {
    if (!str_contains($db, $needle)) {
        throw new RuntimeException('database_contract_missing:'.$needle);
    }
}

if (str_contains($controller, 'LabJobStore')
    || str_contains($controller, 'StemsDnaSync')
    || str_contains($controller, 'createStemsJob')
) {
    throw new RuntimeException('stems_controller_still_uses_legacy_queue');
}

foreach (['queueScientificStemsJob','completeFromJob','failFromJob'] as $needle) {
    if (!str_contains($service, $needle)) {
        throw new RuntimeException('stems_execution_contract_missing:'.$needle);
    }
}

foreach (['StemsDnaExecutionService','progressFromJob','completeFromJob','failFromJob'] as $needle) {
    if (!str_contains($desktop, $needle)) {
        throw new RuntimeException('desktop_stems_callback_missing:'.$needle);
    }
}

if (!str_contains($entry, '"stems"')
    || !str_contains($entry, 'pipeline" / "stems" / "runner.py')
) {
    throw new RuntimeException('worker_entrypoint_stems_dispatch_missing');
}

echo "EZSTUDIO_UNIFIED_LAB_QUEUE_R3B6_CONTRACT_OK\n";
