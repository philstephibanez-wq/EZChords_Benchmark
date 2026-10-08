<?php

namespace App\Controller;

use App\Service\WorkbenchCatalog;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\RedirectResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Attribute\Route;

final class WorkbenchController extends AbstractController
{
    private function songId(Request $request): ?int
    {
        $value = filter_var(
            $request->query->get('song'),
            FILTER_VALIDATE_INT,
            ['options' => ['min_range' => 1]],
        );

        return ($value === false || $value === null) ? null : (int)$value;
    }

    #[Route('/home', name: 'workbench_home', methods: ['GET'])]
    public function home(WorkbenchCatalog $catalog): Response
    {
        return $this->render('workbench/home.html.twig', [
            'songs' => $catalog->songs(),
        ]);
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
    public function stems(Request $request, WorkbenchCatalog $catalog): Response
    {
        $song = $catalog->selectedSong($this->songId($request));

        return $this->render('workbench/stems.html.twig', [
            'songs' => $catalog->songs(),
            'selected_song' => $song,
            'latest_run' => $catalog->latestRun($song),
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
}
