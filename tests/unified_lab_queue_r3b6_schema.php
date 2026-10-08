<?php
declare(strict_types=1);

$root = dirname(__DIR__);
$pdo = new PDO('sqlite:'.$root.'/data/benchmark.sqlite');
$pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

$columns = [];
foreach ($pdo->query("PRAGMA table_info(analysis_jobs)")->fetchAll() as $row) {
    $columns[(string)$row['name']] = $row;
}

foreach (['run_id','scientific_run_id','song_id','source_path','kind','status'] as $name) {
    if (!isset($columns[$name])) {
        throw new RuntimeException('analysis_jobs_column_missing:'.$name);
    }
}
if ((int)$columns['run_id']['notnull'] !== 0) {
    throw new RuntimeException('analysis_jobs_run_id_must_be_nullable');
}

echo "EZSTUDIO_UNIFIED_LAB_QUEUE_R3B6_SCHEMA_OK\n";
