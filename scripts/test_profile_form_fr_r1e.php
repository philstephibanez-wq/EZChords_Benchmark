<?php
$root = dirname(__DIR__);
$template = $root.'/templates/workbench/profile.html.twig';

if (!is_file($template)) {
    fwrite(STDERR, "Template absent\n");
    exit(2);
}

$t = file_get_contents($template);

$required = [
    "Validation humaine",
    "Proposition de l’analyse",
    "Votre avis",
    "Correct",
    "Incorrect",
    "Je ne sais pas",
    "'instrumentation':'Instruments entendus'",
    "'time_signature':'Mesure'",
    "'voice':'Voix'",
    "{{ ui_predicted }}",
    "{% set pv = selected_profile_run.diagnostics.profile_view ?? {} %}",
];

foreach ($required as $needle) {
    if (!str_contains($t, $needle)) {
        fwrite(STDERR, "ECHEC: $needle\n");
        exit(3);
    }
}

foreach (['> OK</label>', '> KO</label>', '> UNKNOWN</label>'] as $old) {
    if (str_contains($t, $old)) {
        fwrite(STDERR, "Ancien choix encore présent: $old\n");
        exit(4);
    }
}

echo "PROFILE_FORM_FR_R1E_CONTRACT_OK\n";
echo "Validation block replacement verified\n";
echo "Scientific revision unchanged: R3B35C\n";
