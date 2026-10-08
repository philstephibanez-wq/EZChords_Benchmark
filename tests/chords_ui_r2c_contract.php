<?php

declare(strict_types=1);

$root = dirname(__DIR__);
$view = $root.'/templates/benchmark/view.html.twig';

if (!is_file($view)) {
    throw new RuntimeException('benchmark_view_missing');
}

$src = file_get_contents($view);
if ($src === false) {
    throw new RuntimeException('benchmark_view_unreadable');
}

foreach ([
    '{% block styles %}',
    '.player-panel{display:flex',
    '.volume-control{display:flex!important',
    '.timeline-line{display:grid',
    '.timeline{display:flex;overflow-x:auto',
    '.measure{min-width:auto',
    '.beats{display:flex',
    '.beat{min-width:68px',
    '.beat.current{outline:3px solid #111',
    '.algo-tools{display:flex',
    '.choice{display:flex',
] as $needle) {
    if (!str_contains($src, $needle)) {
        throw new RuntimeException('chords_ui_selector_missing:'.$needle);
    }
}

foreach ([
    'id="master-play"',
    'id="master-stop"',
    'id="mp3-volume"',
    'id="midi-volume"',
    'data-algo-row=',
    'data-timeline=',
    'data-token=',
] as $needle) {
    if (!str_contains($src, $needle)) {
        throw new RuntimeException('benchmark_markup_regression:'.$needle);
    }
}

echo "EZSTUDIO_CHORDS_UI_R2C_CONTRACT_OK\n";
