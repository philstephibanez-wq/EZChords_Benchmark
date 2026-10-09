<?php

namespace App\Controller;

use App\Service\DnaRegistry;
use App\Service\ProfileDnaExecutionService;
use App\Service\ProfileFrenchSummary;
use App\Service\ProfileValidationService;
use App\Service\WorkbenchCatalog;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\RedirectResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Attribute\Route;

final class ProfileController extends AbstractController
{
    private function songId(Request $request): ?int
    {
        $value = filter_var($request->query->get('song'), FILTER_VALIDATE_INT, ['options' => ['min_range' => 1]]);
        return ($value === false || $value === null) ? null : (int)$value;
    }

    #[Route('/workbench/profile', name: 'workbench_profile', methods: ['GET'])]
    public function index(
        Request $request,
        WorkbenchCatalog $catalog,
        DnaRegistry $dna,
        ProfileDnaExecutionService $execution,
        ProfileFrenchSummary $summary,
        ProfileValidationService $validation,
    ): Response {
        $song = $catalog->selectedSong($this->songId($request));
        $runs = [];
        $selected = null;

        if ($song) {
            $seen = [];
            foreach ($song['song_ids'] ?? [(int)$song['id']] as $songId) {
                foreach ($dna->runsForSongItem((int)$songId, 'profile') as $row) {
                    $id = (int)$row['id'];
                    if (isset($seen[$id])) continue;
                    $seen[$id] = true;
                    $full = $dna->run($id);
                    if ($full) $runs[] = $full;
                }
            }
            usort($runs, static fn(array $a, array $b): int => (int)$b['id'] <=> (int)$a['id']);

            $requested = filter_var($request->query->get('run'), FILTER_VALIDATE_INT, ['options' => ['min_range' => 1]]);
            if ($requested !== false && $requested !== null) {
                foreach ($runs as $candidate) {
                    if ((int)$candidate['id'] === (int)$requested) {
                        $selected = $candidate;
                        break;
                    }
                }
            }
            if ($selected === null && $runs !== []) $selected = $runs[0];
        }

        return $this->render('workbench/profile.html.twig', [
            'songs' => $catalog->songs(),
            'selected_song' => $song,
            'profile_runs' => $runs,
            'selected_profile_run' => $selected,
            'profile_job' => $selected ? $execution->jobForRun((int)$selected['id']) : null,
            'profile_summary' => $selected ? $summary->build($selected) : null,
            'profile_validation_subjects' => $selected
                ? $validation->subjectsForRun($selected)
                : [],
            'profile_validations' => $selected
                ? $validation->validationsForRun((int)$selected['id'])
                : [],
            'profile_validation_stats' => $selected
                ? $validation->statsForRun(
                    (int)$selected['id'],
                    array_column(
                        $validation->subjectsForRun($selected),
                        'subject_key'
                    )
                )
                : [
                    'reviewed' => 0,
                    'ok' => 0,
                    'ko' => 0,
                    'unknown' => 0,
                    'known' => 0,
                    'accuracy' => null,
                ],
        ]);
    }

    #[Route(
        '/profile/{id<\d+>}/validate',
        name: 'profile_validate',
        methods: ['POST']
    )]
    public function validate(
        int $id,
        Request $request,
        DnaRegistry $dna,
        ProfileValidationService $validation,
    ): Response {
        $run = $dna->run($id);
        if (!$run || (string)($run['item'] ?? '') !== 'profile') {
            return new Response('Run PROFILE introuvable.', 404);
        }

        $annotations = $request->request->all('annotations');
        try {
            $validation->save(
                $run,
                is_array($annotations) ? $annotations : [],
            );
        } catch (\RuntimeException|\InvalidArgumentException $e) {
            return new Response(
                'Validation refusée : '.htmlspecialchars(
                    $e->getMessage(),
                    ENT_QUOTES
                ),
                409
            );
        }

        return new RedirectResponse(
            $this->generateUrl('workbench_profile', [
                'song' => (int)$run['song_id'],
                'run' => (int)$run['id'],
            ])
        );
    }

    #[Route('/profile/analyze', name: 'profile_analyze', methods: ['POST'])]
    public function analyze(Request $request, WorkbenchCatalog $catalog, DnaRegistry $dna, ProfileDnaExecutionService $execution): Response
    {
        $songId = filter_var($request->request->get('song'), FILTER_VALIDATE_INT, ['options' => ['min_range' => 1]]);
        if ($songId === false || $songId === null) return new Response('Chanson invalide.', 400);

        $song = $catalog->selectedSong((int)$songId);
        if (!$song) return new Response('Chanson introuvable.', 404);

        $source = $catalog->sourcePath($song);
        if ($source === null) return new Response('Source IMPORT indisponible.', 409);

        $run = $dna->createRun(
            (int)$song['id'],
            'profile',
            ['name' => 'ezstudio-profile-genes', 'version' => 'r3b31', 'model' => 'multi-engine-profile-genes'],
            [
                'audio_sha256' => (string)$song['audio_sha256'],
                'output_contract' => 'ezstudio.profile.v1',
                'automatic_next_stage' => false,
            ],
        );

        $execution->queue((int)$run['id'], $source, (string)$song['audio_sha256']);

        return new RedirectResponse($this->generateUrl('workbench_profile', [
            'song' => (int)$song['id'],
            'run' => (int)$run['id'],
        ]));
    }
}
