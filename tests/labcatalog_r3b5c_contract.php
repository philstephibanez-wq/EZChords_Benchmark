<?php
declare(strict_types=1);

$root = dirname(__DIR__);
$catalogPath = $root.'/src/Service/LabCatalog.php';
$stemsControllerPath = $root.'/src/Controller/StemsLabController.php';
$chordsControllerPath = $root.'/src/Controller/ChordsExperimentController.php';

foreach ([$catalogPath,$stemsControllerPath,$chordsControllerPath] as $path) {
    if (!is_file($path)) {
        throw new RuntimeException('missing_file:'.$path);
    }
}

$catalog = file_get_contents($catalogPath);
$stems = file_get_contents($stemsControllerPath);
$chords = file_get_contents($chordsControllerPath);

foreach ([
    'final class LabCatalog',
    'public function songs(): array',
    'public function song(?int $songId): ?array',
    'public function sourcePath(array $song): ?string',
] as $needle) {
    if (!str_contains($catalog, $needle)) {
        throw new RuntimeException('catalog_contract_missing:'.$needle);
    }
}

if (!str_contains($stems, 'use App\\Service\\LabCatalog;')) {
    throw new RuntimeException('stems_controller_labcatalog_import_missing');
}
if (!str_contains($chords, 'use App\\Service\\LabCatalog;')) {
    throw new RuntimeException('chords_controller_labcatalog_import_missing');
}

echo "EZSTUDIO_LABCATALOG_R3B5C_CONTRACT_OK\n";
