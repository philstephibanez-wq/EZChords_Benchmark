<?php
declare(strict_types=1);

$root = dirname(__DIR__);
$profile = file_get_contents($root.'/src/Controller/ProfileController.php');
if ($profile === false) {
    throw new RuntimeException('profile_controller_unreadable');
}

if (!str_contains($profile, 'AnalysisRunRegistry $runRegistry')) {
    throw new RuntimeException('profile_registry_parameter_missing');
}
if (!str_contains($profile, '$runRegistry->runsForSongItem')) {
    throw new RuntimeException('profile_runsForSongItem_registry_call_missing');
}
if (!str_contains($profile, '$runRegistry->run(')) {
    throw new RuntimeException('profile_run_registry_call_missing');
}
if (!str_contains($profile, '$runs = [];')) {
    throw new RuntimeException('profile_local_runs_array_missing');
}
if (str_contains($profile, 'AnalysisRunRegistry $runs')) {
    throw new RuntimeException('profile_registry_runs_collision_still_present');
}
if (str_contains($profile, '$runs->')) {
    throw new RuntimeException('profile_array_used_as_registry');
}

echo "TERMINOLOGY_PRESET_R1_PROFILE_HOTFIX_CONTRACT_OK\n";
echo "Service/local-array name collision removed\n";
