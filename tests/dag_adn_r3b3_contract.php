<?php
declare(strict_types=1);

$root=dirname(__DIR__);
$registry=file_get_contents($root.'/src/Service/DnaRegistry.php');
$controller=file_get_contents($root.'/src/Controller/DnaController.php');
$runTwig=file_get_contents($root.'/templates/dna/run.html.twig');

foreach ([
    'CREATE TABLE IF NOT EXISTS scientific_runs',
    'CREATE TABLE IF NOT EXISTS scientific_run_parents',
    'CREATE TABLE IF NOT EXISTS scientific_artifacts',
    'CREATE TABLE IF NOT EXISTS scientific_run_inputs',
    'artifact_id',
    'sha256',
    'lineage',
    'compareAcrossSongs',
] as $needle) {
    if (!str_contains($registry,$needle)) {
        throw new RuntimeException('registry_missing:'.$needle);
    }
}

foreach ([
    "Route('/dna/song/",
    "Route('/dna/run/",
    "Route('/dna/compare/",
] as $needle) {
    if (!str_contains($controller,$needle)) {
        throw new RuntimeException('controller_missing:'.$needle);
    }
}

foreach ([
    'Ascendance',
    'Entrées sélectionnées',
    'Artefacts',
    'Descendance',
] as $needle) {
    if (!str_contains($runTwig,$needle)) {
        throw new RuntimeException('twig_missing:'.$needle);
    }
}

echo "EZSTUDIO_DAG_ADN_R3B3_CONTRACT_OK\n";
