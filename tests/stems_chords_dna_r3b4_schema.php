<?php
declare(strict_types=1);

require dirname(__DIR__).'/vendor/autoload.php';

use App\Service\Database;
use App\Service\DnaRegistry;

$root=dirname(__DIR__);
$db=new Database($root.DIRECTORY_SEPARATOR.'data'.DIRECTORY_SEPARATOR.'benchmark.sqlite');
$dna=new DnaRegistry($db);
$dna->ensureSchema();

$required=[
 'scientific_runs','scientific_run_parents','scientific_artifacts',
 'scientific_run_inputs','scientific_run_aliases','scientific_run_labels'
];

$stmt=$db->pdo()->prepare(
 "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
);
foreach($required as $table){
 $stmt->execute([$table]);
 if($stmt->fetchColumn()===false) throw new RuntimeException('missing_table:'.$table);
}

echo "EZSTUDIO_STEMS_CHORDS_DNA_R3B4_SCHEMA_OK\n";
