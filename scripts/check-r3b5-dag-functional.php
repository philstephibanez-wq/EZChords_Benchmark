<?php
declare(strict_types=1);

require dirname(__DIR__).'/vendor/autoload.php';

use App\Service\Database;
use App\Service\DnaRegistry;

$root = dirname(__DIR__);
$db = new Database($root.DIRECTORY_SEPARATOR.'data'.DIRECTORY_SEPARATOR.'benchmark.sqlite');
$dna = new DnaRegistry($db);

$statePath = 'H:\temp\EZStudio_lab\r3b5-dag-functional-test.json';
if (!is_file($statePath)) {
    fwrite(STDERR, "Missing state file: {$statePath}\n");
    exit(2);
}

$state = json_decode((string)file_get_contents($statePath), true);
if (!is_array($state) || ($state['schema'] ?? '') !== 'ezstudio.r3b5-dag-functional-test.v1') {
    fwrite(STDERR, "Invalid state file.\n");
    exit(3);
}

$parentId = (int)$state['parent_stems_run_id'];
$runAId = (int)$state['run_a']['scientific_run_id'];
$runBId = (int)$state['run_b']['scientific_run_id'];
$jobAId = (int)$state['run_a']['job_id'];
$jobBId = (int)$state['run_b']['job_id'];
$benchAId = (int)$state['run_a']['benchmark_run_id'];
$benchBId = (int)$state['run_b']['benchmark_run_id'];

$runA = $dna->run($runAId);
$runB = $dna->run($runBId);
if (!$runA || !$runB) {
    throw new RuntimeException('scientific_runs_missing');
}

$parentA = array_values(array_filter(
    $runA['parents'],
    static fn(array $p): bool => (string)$p['role'] === 'stems_source'
));
$parentB = array_values(array_filter(
    $runB['parents'],
    static fn(array $p): bool => (string)$p['role'] === 'stems_source'
));
if (count($parentA) !== 1 || count($parentB) !== 1) {
    throw new RuntimeException('stems_parent_cardinality_invalid');
}
if ((int)$parentA[0]['id'] !== $parentId || (int)$parentB[0]['id'] !== $parentId) {
    throw new RuntimeException('runs_do_not_share_expected_parent');
}

$getInputs = static function(array $run, string $role): array {
    $rows = array_values(array_filter(
        $run['inputs'],
        static fn(array $a): bool => (string)$a['input_role'] === $role
    ));
    $roles = array_map(static fn(array $a): string => (string)$a['role'], $rows);
    sort($roles);
    return $roles;
};

$aChord = $getInputs($runA, 'chord_input');
$bChord = $getInputs($runB, 'chord_input');
$aN = $getInputs($runA, 'no_chord_evidence');
$bN = $getInputs($runB, 'no_chord_evidence');

if ($aChord === $bChord) {
    throw new RuntimeException('chord_selections_not_different');
}
if ($aN !== $bN) {
    throw new RuntimeException('no_chord_selections_should_match');
}

foreach ([$runA,$runB] as $run) {
    foreach ($run['inputs'] as $artifact) {
        $path = (string)$artifact['path'];
        $expected = strtolower((string)$artifact['sha256']);
        if (!is_file($path)) {
            throw new RuntimeException('selected_artifact_missing:'.$path);
        }
        $actual = strtolower((string)hash_file('sha256', $path));
        if ($actual !== $expected) {
            throw new RuntimeException('selected_artifact_hash_mismatch:'.$artifact['artifact_id']);
        }
    }
}

$jobA = $db->analysisJob($jobAId);
$jobB = $db->analysisJob($jobBId);
if (!$jobA || !$jobB) {
    throw new RuntimeException('analysis_jobs_missing');
}
if ((string)$jobA['kind'] !== 'chords_scientific' || (string)$jobB['kind'] !== 'chords_scientific') {
    throw new RuntimeException('analysis_job_kind_invalid');
}
if ($jobAId === $jobBId || $benchAId === $benchBId || $runAId === $runBId) {
    throw new RuntimeException('branch_identity_not_distinct');
}

echo "R3B5 DAG branch identities:\n";
echo "  parent STEMS: {$state['parent_stems_public_id']} (#{$parentId})\n";
echo "  A: {$state['run_a']['public_id']} job={$jobAId} benchmark={$benchAId} state={$runA['state']} job_state={$jobA['status']}\n";
echo "  B: {$state['run_b']['public_id']} job={$jobBId} benchmark={$benchBId} state={$runB['state']} job_state={$jobB['status']}\n";
echo "  A chord_input=".implode(',', $aChord)."\n";
echo "  B chord_input=".implode(',', $bChord)."\n";
echo "  A no_chord=".implode(',', $aN)."\n";
echo "  B no_chord=".implode(',', $bN)."\n";

$done = true;
foreach ([[$runA,$jobA,$benchAId,'A'],[$runB,$jobB,$benchBId,'B']] as [$run,$job,$benchId,$label]) {
    $benchmark = $db->run((int)$benchId);
    $isDone = (string)$run['state'] === 'done'
        && (string)$job['status'] === 'done'
        && is_array($benchmark)
        && (string)$benchmark['status'] === 'done';

    if (!$isDone) {
        $done = false;
        echo "WAIT {$label}: scientific={$run['state']} job={$job['status']} benchmark="
            .($benchmark['status'] ?? 'missing')."\n";
        continue;
    }

    $result = json_decode((string)$benchmark['result_json'], true);
    if (!is_array($result)) {
        throw new RuntimeException("benchmark_result_invalid_{$label}");
    }
    if (($result['analysis_source'] ?? null) !== 'selected_stems') {
        throw new RuntimeException("analysis_source_not_selected_stems_{$label}");
    }

    $selection = $result['no_chord_benchmark']['scientific_selection'] ?? null;
    if (!is_array($selection) || ($selection['schema'] ?? '') !== 'ezstudio.chords.selection.v1') {
        throw new RuntimeException("scientific_selection_missing_{$label}");
    }

    $active = (string)($result['no_chord_benchmark']['active_variant'] ?? '');
    if ($active !== 'E_positive_harmonic_support_selected') {
        throw new RuntimeException("selected_no_chord_variant_not_active_{$label}:{$active}");
    }
}

if (!$done) {
    echo "EZSTUDIO_R3B5_DAG_TEST_PENDING\n";
    exit(10);
}

echo "EZSTUDIO_R3B5_DAG_FUNCTIONAL_OK\n";
