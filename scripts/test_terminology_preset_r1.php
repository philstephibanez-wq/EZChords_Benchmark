<?php
$root = dirname(__DIR__);
$checks = [
    $root.'/src/Service/AnalysisRunRegistry.php' => 'class AnalysisRunRegistry extends DnaRegistry',
    $root.'/src/Service/PresetRegistry.php' => 'class PresetRegistry extends GenomeRegistry',
    $root.'/src/Service/DnaRegistry.php' => 'class DnaRegistry',
    $root.'/src/Service/GenomeRegistry.php' => 'class GenomeRegistry',
];
foreach ($checks as $path => $needle) {
    if (!is_file($path)) {
        fwrite(STDERR, "missing: ".$path.PHP_EOL);
        exit(1);
    }
    $text = file_get_contents($path);
    if (!str_contains($text, $needle)) {
        fwrite(STDERR, "missing marker: ".$needle." in ".$path.PHP_EOL);
        exit(2);
    }
}
echo "TERMINOLOGY_PRESET_R1_PHP_CONTRACT_OK\n";
echo "Canonical registry facades present; legacy persistence retained\n";
