<?php
declare(strict_types=1);

$root = dirname(__DIR__);
$iterator = new RecursiveIteratorIterator(
    new RecursiveDirectoryIterator(
        $root.'/src',
        FilesystemIterator::SKIP_DOTS
    )
);

$violations = [];
$registryUsers = 0;

foreach ($iterator as $file) {
    if (!$file->isFile() || strtolower($file->getExtension()) !== 'php') {
        continue;
    }

    $path = $file->getPathname();
    $text = file_get_contents($path);
    if ($text === false) {
        throw new RuntimeException('unreadable:'.$path);
    }

    if (str_contains($text, 'AnalysisRunRegistry')) {
        $registryUsers++;

        if (str_contains($text, 'AnalysisRunRegistry $runs')) {
            $violations[] = $path.':parameter_collision';
        }

        if (str_contains($text, '$this->runs->')) {
            $violations[] = $path.':stale_property_runs';
        }
    }
}

if ($violations !== []) {
    throw new RuntimeException(
        "registry_property_violations:\n".implode("\n", $violations)
    );
}

$profile = file_get_contents($root.'/src/Service/ProfileDnaExecutionService.php');
if ($profile === false) {
    throw new RuntimeException('profile_execution_service_unreadable');
}

foreach ([
    'AnalysisRunRegistry $runRegistry',
    '$this->runRegistry->run(',
    '$this->runRegistry->setAlias(',
    '$this->runRegistry->setLabel(',
    '$this->runRegistry->setState(',
    '$this->runRegistry->registerArtifact(',
] as $needle) {
    if (!str_contains($profile, $needle)) {
        throw new RuntimeException(
            'profile_execution_registry_marker_missing:'.$needle
        );
    }
}

if (str_contains($profile, '$this->runs->')) {
    throw new RuntimeException('profile_execution_stale_runs_property');
}

echo "TERMINOLOGY_PRESET_R1_REGISTRY_PROPERTY_HOTFIX_CONTRACT_OK\n";
echo "Registry users checked: ".$registryUsers."\n";
echo "No stale \$this->runs registry access remains\n";
