<?php
declare(strict_types=1);

$root=dirname(__DIR__);
$dna=file_get_contents($root.'/src/Service/DnaRegistry.php');
$sync=file_get_contents($root.'/src/Service/StemsDnaSync.php');
$chords=file_get_contents($root.'/src/Service/ChordsExperimentService.php');
$controller=file_get_contents($root.'/src/Controller/ChordsExperimentController.php');
$stemsController=file_get_contents($root.'/src/Controller/StemsLabController.php');
$jobStore=file_get_contents($root.'/src/Service/LabJobStore.php');
$twig=file_get_contents($root.'/templates/lab/chords_experiment.html.twig');

foreach ([
 'findByAlias','setState','artifactsForRun','runsForSongItem'
] as $needle) {
 if(!str_contains($dna,$needle)) throw new RuntimeException('dna_missing:'.$needle);
}
foreach ([
 'lead_vocals','backing_vocals','hash_file(\'sha256\'','registerArtifact'
] as $needle) {
 if(!str_contains($sync,$needle)) throw new RuntimeException('sync_missing:'.$needle);
}
foreach ([
 'chord_input','no_chord_evidence','execution_contract',
 'ezstudio.chords.selection.v1','parent_stems_run_id'
] as $needle) {
 if(!str_contains($chords,$needle)) throw new RuntimeException('chords_missing:'.$needle);
}
foreach ([
 "Route('/chords/experiment'","Route('/chords/experiment/create'"
] as $needle) {
 if(!str_contains($controller,$needle)) throw new RuntimeException('controller_missing:'.$needle);
}
foreach ([
 'technical_job_id','StemsDnaSync','setAlias','setState'
] as $needle) {
 if(!str_contains($stemsController,$needle)) throw new RuntimeException('stems_controller_missing:'.$needle);
}
foreach ([
 "'scientific_run_id' =>",
 "'lineage' =>",
 "'parent_stems_job_id' =>"
] as $needle) {
 if(!str_contains($jobStore,$needle)) throw new RuntimeException('job_store_missing:'.$needle);
}
foreach ([
 'CHORDS — matrice',
 'chord_inputs[]','no_chord_inputs[]','Run STEMS parent'
] as $needle) {
 if(!str_contains($twig,$needle)) throw new RuntimeException('twig_missing:'.$needle);
}

echo "EZSTUDIO_STEMS_CHORDS_DNA_R3B4_CONTRACT_OK\n";
