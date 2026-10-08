<?php
declare(strict_types=1);

require dirname(__DIR__).'/vendor/autoload.php';

use App\Service\Database;

$projectDir = dirname(__DIR__);
$databasePath = $projectDir.DIRECTORY_SEPARATOR.'data'.DIRECTORY_SEPARATOR.'benchmark.sqlite';
$db = new Database($databasePath);

$required = [
    'scientific_runs',
    'scientific_run_parents',
    'scientific_artifacts',
    'scientific_run_inputs',
    'scientific_run_aliases',
    'scientific_run_labels',
];

$stmt = $db->pdo()->prepare(
    "SELECT name FROM sqlite_master
     WHERE type='table' AND name=?"
);

foreach ($required as $table) {
    $stmt->execute([$table]);
    if ($stmt->fetchColumn() === false) {
        throw new RuntimeException('missing_schema_table:'.$table);
    }
}

echo "EZSTUDIO_DAG_ADN_R3B3_SCHEMA_CONTRACT_OK\n";
