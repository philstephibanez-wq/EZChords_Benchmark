<?php
declare(strict_types=1);

require dirname(__DIR__).'/vendor/autoload.php';

use App\Service\ChordsDnaExecutionService;
use App\Service\ChordsExperimentService;
use App\Service\Database;
use App\Service\DnaRegistry;
use App\Service\LabJobStore;
use App\Service\StemsDnaSync;

$root = dirname(__DIR__);
$db = new Database($root.DIRECTORY_SEPARATOR.'data'.DIRECTORY_SEPARATOR.'benchmark.sqlite');
$dna = new DnaRegistry($db);
$experiments = new ChordsExperimentService($dna, $root);
$execution = new ChordsDnaExecutionService($db, $dna);

/*
 * R3B5A:
 * R3B4 synchronizes legacy/current filesystem STEMS jobs lazily when the STEMS
 * page is opened. The functional test must not depend on an UI visit.
 * Synchronize the real LAB STEMS job history first.
 */
$jobStore = new LabJobStore();
$stemsSync = new StemsDnaSync($dna);
$stemJobs = array_values(array_filter(
    $jobStore->all(),
    static fn(array $job): bool => (string)($job['kind'] ?? '') === 'stems'
));

$syncStats = [
    'total' => count($stemJobs),
    'done' => 0,
    'synced' => 0,
    'done_with_artifacts' => 0,
    'details' => [],
];

foreach ($stemJobs as $job) {
    $jobId = (int)($job['job_id'] ?? 0);
    $state = (string)($job['state'] ?? '');
    if ($state === 'done') {
        $syncStats['done']++;
    }

    $run = null;
    $syncError = null;
    try {
        $run = $stemsSync->sync($job);
    } catch (Throwable $e) {
        $syncError = get_class($e).': '.$e->getMessage();
    }

    if (is_array($run)) {
        $syncStats['synced']++;
        $artifactCount = count($run['artifacts'] ?? []);
        if ((string)($run['state'] ?? '') === 'done' && $artifactCount > 0) {
            $syncStats['done_with_artifacts']++;
        }
    } else {
        $artifactCount = 0;
    }

    $result = is_array($job['result'] ?? null) ? $job['result'] : [];
    $runDir = trim((string)($result['run_dir'] ?? ''));
    $syncStats['details'][] = [
        'job_id' => $jobId,
        'job_state' => $state,
        'song_id' => $job['song_id'] ?? null,
        'audio_hash' => $job['request']['audio_hash'] ?? null,
        'run_dir' => $runDir,
        'run_dir_exists' => $runDir !== '' && is_dir($runDir),
        'scientific_run' => is_array($run) ? ($run['public_id'] ?? null) : null,
        'scientific_state' => is_array($run) ? ($run['state'] ?? null) : null,
        'artifact_count' => $artifactCount,
        'sync_error' => $syncError,
    ];
}

echo "STEMS sync: total={$syncStats['total']} done={$syncStats['done']} synced={$syncStats['synced']} done_with_artifacts={$syncStats['done_with_artifacts']}\n";

$options = getopt('', ['song-id::']);
$songId = isset($options['song-id']) ? (int)$options['song-id'] : 0;

if ($songId <= 0) {
    $stmt = $db->pdo()->query(
        "SELECT sr.song_id
         FROM scientific_runs sr
         WHERE sr.item='stems' AND sr.state='done'
         ORDER BY sr.id DESC"
    );
    foreach ($stmt->fetchAll() as $row) {
        $candidate = (int)$row['song_id'];
        $runs = $experiments->stemsRuns($candidate);
        if ($runs !== []) {
            $songId = $candidate;
            break;
        }
    }
}

if ($songId <= 0) {
    echo "No usable STEMS ADN run after synchronization.\n";
    foreach ($syncStats['details'] as $detail) {
        echo sprintf(
            "  job=%d state=%s song=%s run_dir=%s exists=%s dna=%s dna_state=%s artifacts=%d%s\n",
            (int)$detail['job_id'],
            (string)$detail['job_state'],
            $detail['song_id'] === null ? 'null' : (string)$detail['song_id'],
            (string)($detail['run_dir'] ?: '—'),
            $detail['run_dir_exists'] ? 'yes' : 'no',
            (string)($detail['scientific_run'] ?: '—'),
            (string)($detail['scientific_state'] ?: '—'),
            (int)$detail['artifact_count'],
            $detail['sync_error'] ? ' error='.$detail['sync_error'] : '',
        );
    }
    fwrite(
        STDERR,
        "A completed STEMS job with persistent run_dir and artifacts is required before the DAG CHORDS functional test.\n"
    );
    exit(2);
}

$stemsRuns = $experiments->stemsRuns($songId);
if ($stemsRuns === []) {
    fwrite(STDERR, "No completed STEMS run for song_id={$songId} after synchronization.\n");
    exit(3);
}

$parent = $stemsRuns[0];
$byRole = [];
foreach ($parent['artifacts'] as $artifact) {
    $byRole[(string)$artifact['role']] = $artifact;
}

$required = ['bass','guitar','piano','other'];
foreach ($required as $role) {
    if (!isset($byRole[$role])) {
        fwrite(
            STDERR,
            "Selected STEMS run {$parent['public_id']} is missing harmonic artifact: {$role}\n"
        );
        exit(4);
    }
}

$allHarmonic = array_map(
    static fn(string $role): string => (string)$byRole[$role]['artifact_id'],
    $required
);

$reducedChord = [
    (string)$byRole['bass']['artifact_id'],
    (string)$byRole['guitar']['artifact_id'],
];

$runA = $experiments->createConfiguredRun(
    $songId,
    (int)$parent['id'],
    $allHarmonic,
    $allHarmonic,
    'lv-chordia',
    'Auto',
);
$queuedA = $execution->queue((int)$runA['id']);

$runB = $experiments->createConfiguredRun(
    $songId,
    (int)$parent['id'],
    $reducedChord,
    $allHarmonic,
    'lv-chordia',
    'Auto',
);
$queuedB = $execution->queue((int)$runB['id']);

if ((int)$queuedA['job_id'] === (int)$queuedB['job_id']) {
    throw new RuntimeException('jobs_not_distinct');
}
if ((int)$queuedA['benchmark_run_id'] === (int)$queuedB['benchmark_run_id']) {
    throw new RuntimeException('benchmark_runs_not_distinct');
}

$state = [
    'schema' => 'ezstudio.r3b5-dag-functional-test.v1',
    'created_at' => gmdate('c'),
    'song_id' => $songId,
    'parent_stems_run_id' => (int)$parent['id'],
    'parent_stems_public_id' => (string)$parent['public_id'],
    'run_a' => [
        'scientific_run_id' => (int)$runA['id'],
        'public_id' => (string)$runA['public_id'],
        'job_id' => (int)$queuedA['job_id'],
        'benchmark_run_id' => (int)$queuedA['benchmark_run_id'],
        'chord_roles' => ['bass','guitar','piano','other'],
        'no_chord_roles' => ['bass','guitar','piano','other'],
    ],
    'run_b' => [
        'scientific_run_id' => (int)$runB['id'],
        'public_id' => (string)$runB['public_id'],
        'job_id' => (int)$queuedB['job_id'],
        'benchmark_run_id' => (int)$queuedB['benchmark_run_id'],
        'chord_roles' => ['bass','guitar'],
        'no_chord_roles' => ['bass','guitar','piano','other'],
    ],
];

$stateRoot = 'H:\temp\EZStudio_lab';
if (!is_dir($stateRoot) && !mkdir($stateRoot, 0777, true) && !is_dir($stateRoot)) {
    throw new RuntimeException('state_root_create_failed');
}
$statePath = $stateRoot.DIRECTORY_SEPARATOR.'r3b5-dag-functional-test.json';
file_put_contents(
    $statePath,
    json_encode($state, JSON_PRETTY_PRINT|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES)."\n",
    LOCK_EX
);

echo "EZSTUDIO_R3B5A_STEMS_HISTORY_SYNC_OK\n";
echo "EZSTUDIO_R3B5_DAG_TEST_PREPARE_OK\n";
echo "song_id={$songId}\n";
echo "parent_stems={$parent['public_id']}\n";
echo "run_a={$runA['public_id']} job={$queuedA['job_id']} benchmark={$queuedA['benchmark_run_id']}\n";
echo "run_b={$runB['public_id']} job={$queuedB['job_id']} benchmark={$queuedB['benchmark_run_id']}\n";
echo "state={$statePath}\n";
