<?php

namespace App\Controller;

use App\Service\Database;
use App\Service\DnaRegistry;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Attribute\Route;

final class DnaController extends AbstractController
{
    #[Route('/dna/song/{id<\d+>}', name: 'dna_song', methods: ['GET'])]
    public function song(int $id, Database $db, DnaRegistry $dna): Response
    {
        $stmt = $db->pdo()->prepare(
            'SELECT * FROM songs WHERE id=?'
        );
        $stmt->execute([$id]);
        $song = $stmt->fetch();

        if (!$song) {
            throw $this->createNotFoundException();
        }

        return $this->render('dna/song.html.twig', [
            'song' => $song,
            'runs' => $dna->runsForSong($id),
        ]);
    }

    #[Route('/dna/run/{id<\d+>}', name: 'dna_run', methods: ['GET'])]
    public function run(int $id, DnaRegistry $dna): Response
    {
        $run = $dna->run($id);
        if (!$run) {
            throw $this->createNotFoundException();
        }

        return $this->render('dna/run.html.twig', [
            'run' => $run,
            'lineage' => $dna->lineage($id),
        ]);
    }

    #[Route('/dna/run/{id<\d+>}.json', name: 'dna_run_json', methods: ['GET'])]
    public function runJson(int $id, DnaRegistry $dna): JsonResponse
    {
        $run = $dna->run($id);
        if (!$run) {
            return new JsonResponse(['error' => 'run_not_found'], 404);
        }

        return new JsonResponse([
            'run' => $run,
            'lineage' => $dna->lineage($id),
        ]);
    }

    #[Route('/dna/compare/{item<stems|chords|lyrics>}', name: 'dna_compare', methods: ['GET'])]
    public function compare(string $item, DnaRegistry $dna): Response
    {
        return $this->render('dna/compare.html.twig', [
            'item' => $item,
            'rows' => $dna->compareAcrossSongs($item),
        ]);
    }
}
