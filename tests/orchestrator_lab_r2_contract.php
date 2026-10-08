<?php

declare(strict_types=1);

$root = dirname(__DIR__);

$files = [
    $root.'/src/Controller/AnalysisDesktopController.php',
    $root.'/src/Service/LabAnalysisTokenGuard.php',
    $root.'/src/Service/Database.php',
    $root.'/src/Service/BenchmarkLauncher.php',
];

foreach ($files as $file) {
    if (!is_file($file)) {
        throw new RuntimeException('missing_file:'.$file);
    }
}

$db = file_get_contents($root.'/src/Service/Database.php');
$launcher = file_get_contents($root.'/src/Service/BenchmarkLauncher.php');
$controller = file_get_contents($root.'/src/Controller/AnalysisDesktopController.php');
$guard = file_get_contents($root.'/src/Service/LabAnalysisTokenGuard.php');

$requiredDb = [
    'CREATE TABLE IF NOT EXISTS analysis_jobs',
    'public function queueAnalysisJob(',
    'public function analysisQueue(',
    'public function claimNextAnalysisJob(',
    'public function analysisJobContext(',
    'public function updateAnalysisJobProgress(',
    'public function completeAnalysisJob(',
    'public function failAnalysisJob(',
    "'protocol' => 'ezscore.analysis-job.v2'",
    "'benchmark',",
    "'kind' => (string)",
    "\$job['kind']",
];

foreach ($requiredDb as $needle) {
    if (!str_contains($db, $needle)) {
        throw new RuntimeException('database_contract_missing:'.$needle);
    }
}

if (!str_contains($launcher, 'queueAnalysisJob($runId, $audioPath, $signature)')) {
    throw new RuntimeException('launcher_does_not_queue');
}

$launchStart = strpos($launcher, 'public function launch');
$launchEnd = strpos($launcher, '/**', $launchStart);
if ($launchStart === false || $launchEnd === false) {
    throw new RuntimeException('launcher_method_bounds_missing');
}
$launchMethod = substr($launcher, $launchStart, $launchEnd - $launchStart);
if (str_contains($launchMethod, 'launchDetachedWindows')) {
    throw new RuntimeException('launcher_still_spawns_local_worker');
}

foreach ([
    '/jobs/queue',
    '/jobs/claim',
    '/jobs/{id<\d+>}/progress',
    '/jobs/{id<\d+>}/complete',
    '/jobs/{id<\d+>}/fail',
] as $needle) {
    if (!str_contains($controller, $needle)) {
        throw new RuntimeException('controller_route_missing:'.$needle);
    }
}

if (!str_contains($guard, 'X-EZScore-Analysis-Token')) {
    throw new RuntimeException('token_header_contract_missing');
}
if (!str_contains($guard, 'EZSTUDIO_ANALYSIS_WORKER_TOKEN')) {
    throw new RuntimeException('lab_token_contract_missing');
}

echo "EZSTUDIO_ORCHESTRATOR_LAB_R2B_PHP_CONTRACT_OK\n";
