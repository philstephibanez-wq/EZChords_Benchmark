<?php

namespace App\Controller;

use App\Service\DnaRegistry;
use App\Service\CatalogService;
use App\Service\Database;
use App\Service\WorkbenchCatalog;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\RedirectResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Attribute\Route;

final class WorkbenchController extends AbstractController
{
    private const AUDIO_EXTENSIONS = ['wav','mp3','flac','ogg','oga','m4a','aac'];

    private function songId(Request $request): ?int
    {
        $value = filter_var(
            $request->query->get('song'),
            FILTER_VALIDATE_INT,
            ['options' => ['min_range' => 1]],
        );

        return ($value === false || $value === null) ? null : (int)$value;
    }

    private function runId(Request $request): ?int
    {
        $value = filter_var(
            $request->query->get('run'),
            FILTER_VALIDATE_INT,
            ['options' => ['min_range' => 1]],
        );

        return ($value === false || $value === null) ? null : (int)$value;
    }

    #[Route('/home', name: 'workbench_home', methods: ['GET'])]
    public function home(CatalogService $catalog): Response
    {
        return $this->render('workbench/home.html.twig', [
            'songs' => $catalog->songs(),
        ]);
    }

    #[Route('/analysis/jobs/{id<\d+>}/cancel', name: 'analysis_job_cancel', methods: ['POST'])]
    public function cancelAnalysisJob(
        int $id,
        Request $request,
        Database $db,
    ): Response {
        try {
            $job = $db->requestAnalysisJobCancellation($id);
        } catch (\RuntimeException $e) {
            return new Response($e->getMessage(), 409);
        }

        if ($request->isXmlHttpRequest()) {
            return $this->json([
                'job_id' => (int)($job['id'] ?? $id),
                'status' => (string)($job['status'] ?? ''),
                'progress' => (int)($job['progress'] ?? 0),
            ]);
        }

        return new RedirectResponse($this->generateUrl('workbench_home'));
    }

    #[Route('/import', name: 'workbench_import', methods: ['GET'])]
    public function import(Request $request, WorkbenchCatalog $catalog): Response
    {
        return $this->render('workbench/import.html.twig', [
            'songs' => $catalog->songs(),
            'selected_song' => $catalog->selectedSong($this->songId($request)),
        ]);
    }

    #[Route('/workbench/stems', name: 'workbench_stems', methods: ['GET'])]
    public function stems(
        Request $request,
        WorkbenchCatalog $catalog,
        DnaRegistry $dna,
    ): Response {
        $song = $catalog->selectedSong($this->songId($request));
        $runs = [];
        $selectedRun = null;

        if ($song) {
            $seen = [];
            foreach ($song['song_ids'] ?? [(int)$song['id']] as $songId) {
                foreach ($dna->runsForSongItem((int)$songId, 'stems') as $row) {
                    $id = (int)$row['id'];
                    if (isset($seen[$id])) {
                        continue;
                    }
                    $seen[$id] = true;
                    $full = $dna->run($id);
                    if ($full) {
                        $full['audio_artifacts'] = $this->audioArtifacts(
                            $full['artifacts'] ?? []
                        );
                        $runs[] = $full;
                    }
                }
            }

            usort(
                $runs,
                static fn(array $a, array $b): int => (int)$b['id'] <=> (int)$a['id']
            );

            $requestedRunId = $this->runId($request);
            foreach ($runs as $candidate) {
                if ($requestedRunId !== null && (int)$candidate['id'] === $requestedRunId) {
                    $selectedRun = $candidate;
                    break;
                }
            }

            if ($selectedRun === null) {
                foreach ($runs as $candidate) {
                    if (
                        (string)$candidate['state'] === 'done'
                        && ($candidate['audio_artifacts'] ?? []) !== []
                    ) {
                        $selectedRun = $candidate;
                        break;
                    }
                }
            }

            if ($selectedRun === null && $runs !== []) {
                $selectedRun = $runs[0];
            }
        }

        return $this->render('workbench/stems.html.twig', [
            'songs' => $catalog->songs(),
            'selected_song' => $song,
            'latest_run' => $catalog->latestRun($song),
            'stems_runs' => $runs,
            'selected_stems_run' => $selectedRun,
        ]);
    }

    #[Route('/workbench/chords', name: 'workbench_chords', methods: ['GET'])]
    public function chords(Request $request, WorkbenchCatalog $catalog): Response
    {
        $song = $catalog->selectedSong($this->songId($request));
        $run = $catalog->latestChordsRun($song);

        if ($run === null) {
            return $this->render('workbench/no_chords.html.twig', [
                'songs' => $catalog->songs(),
                'selected_song' => $song,
            ]);
        }

        return new RedirectResponse(
            $this->generateUrl('bench_view', ['id' => (int)$run['id']])
        );
    }

    #[Route('/workbench/lyrics', name: 'workbench_lyrics', methods: ['GET'])]
    public function lyrics(Request $request, WorkbenchCatalog $catalog): Response
    {
        $song = $catalog->selectedSong($this->songId($request));

        return $this->render('workbench/lyrics.html.twig', [
            'songs' => $catalog->songs(),
            'selected_song' => $song,
            'latest_run' => $catalog->latestRun($song),
        ]);
    }

    #[Route('/workbench/runs', name: 'workbench_runs', methods: ['GET'])]
    public function runs(Request $request, WorkbenchCatalog $catalog): Response
    {
        $song = $catalog->selectedSong($this->songId($request));

        return $this->render('workbench/runs.html.twig', [
            'songs' => $catalog->songs(),
            'selected_song' => $song,
            'runs' => $song['runs'] ?? [],
        ]);
    }

    private function audioArtifacts(array $artifacts): array
    {
        $out = [];

        foreach ($artifacts as $artifact) {
            $path = trim((string)($artifact['path'] ?? ''));
            $ext = strtolower(pathinfo($path, PATHINFO_EXTENSION));
            if ($path === '' || !in_array($ext, self::AUDIO_EXTENSIONS, true)) {
                continue;
            }

            $metadata = json_decode((string)($artifact['metadata_json'] ?? ''), true);
            if (!is_array($metadata)) {
                $metadata = [];
            }

            $role = (string)($artifact['role'] ?? 'audio');
            $artifact['metadata'] = $metadata;
            $artifact['group'] = $this->artifactGroup($role, $metadata);
            $artifact['harmonic_default'] = $this->harmonicDefault($role, $metadata);
            $artifact['display_label'] = $this->displayLabel($role, $metadata);
            $artifact['confidence'] = $this->confidence($metadata);

            $out[] = $artifact;
        }

        usort($out, static function(array $a, array $b): int {
            $groups = ['vocals'=>0,'rhythm'=>1,'bass'=>2,'guitar'=>3,'keys'=>4,'strings'=>5,'winds'=>6,'plucked'=>7,'other'=>8];
            $ga = $groups[(string)$a['group']] ?? 99;
            $gb = $groups[(string)$b['group']] ?? 99;
            return $ga <=> $gb ?: strcasecmp((string)$a['display_label'], (string)$b['display_label']);
        });

        return $out;
    }

    private function artifactGroup(string $role, array $metadata): string
    {
        $taxonomy = strtolower((string)($metadata['taxonomy_group'] ?? ''));
        if ($taxonomy !== '') {
            return $taxonomy;
        }

        $r = strtolower($role);
        if (str_contains($r, 'vocal') || str_contains($r, 'voice')) return 'vocals';
        if (str_contains($r, 'drum') || str_contains($r, 'kick') || str_contains($r, 'snare')
            || str_contains($r, 'cymbal') || str_contains($r, 'percussion') || str_contains($r, 'hi_hat')) return 'rhythm';
        if (str_contains($r, 'bass') || str_contains($r, 'contrabass')) return 'bass';
        if (str_contains($r, 'guitar')) return 'guitar';
        if (str_contains($r, 'piano') || str_contains($r, 'organ') || str_contains($r, 'synth')
            || str_contains($r, 'keys')) return 'keys';
        if (str_contains($r, 'violin') || str_contains($r, 'viola') || str_contains($r, 'cello')
            || str_contains($r, 'string')) return 'strings';
        if (str_contains($r, 'flute') || str_contains($r, 'sax') || str_contains($r, 'brass')
            || str_contains($r, 'reed') || str_contains($r, 'wind')) return 'winds';
        if (str_contains($r, 'banjo') || str_contains($r, 'mandolin') || str_contains($r, 'ukulele')
            || str_contains($r, 'harp') || str_contains($r, 'pluck')) return 'plucked';
        return 'other';
    }

    private function harmonicDefault(string $role, array $metadata): bool
    {
        if (array_key_exists('harmonic_default', $metadata)) {
            return (bool)$metadata['harmonic_default'];
        }

        return in_array(
            $this->artifactGroup($role, $metadata),
            ['bass','guitar','keys','strings','winds','plucked','other'],
            true
        );
    }

    private function displayLabel(string $role, array $metadata): string
    {
        foreach (['instrument_label','taxonomy_label','display_label'] as $key) {
            $value = trim((string)($metadata[$key] ?? ''));
            if ($value !== '') {
                return $value;
            }
        }

        return ucwords(str_replace(['_','-'], ' ', $role));
    }

    private function confidence(array $metadata): ?float
    {
        foreach (['instrument_confidence','classifier_confidence','confidence'] as $key) {
            if (isset($metadata[$key]) && is_numeric($metadata[$key])) {
                return max(0.0, min(1.0, (float)$metadata[$key]));
            }
        }
        return null;
    }
}
