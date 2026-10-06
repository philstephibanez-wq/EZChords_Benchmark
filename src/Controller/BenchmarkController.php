<?php
namespace App\Controller;

use App\Service\BenchmarkLauncher;
use App\Service\Database;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\File\UploadedFile;
use Symfony\Component\HttpFoundation\RedirectResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Attribute\Route;

final class BenchmarkController extends AbstractController
{
    #[Route('/', name: 'bench_index', methods: ['GET'])]
    public function index(Database $db): Response
    {
        return $this->render('benchmark/index.html.twig', [
            'runs' => $db->allRuns(),
            'scores' => $db->globalScores(),
        ]);
    }

    #[Route('/run', name: 'bench_start', methods: ['POST'])]
    public function start(
        Request $request,
        Database $db,
        BenchmarkLauncher $launcher
    ): Response {
        /** @var UploadedFile|null $audio */
        $audio = $request->files->get('audio');

        if (!$audio instanceof UploadedFile || !$audio->isValid()) {
            return new Response('Fichier audio invalide.', 400);
        }

        $signature = (string)$request->request->get('signature', 'Auto');
        $allowed = ['Auto','2/4','3/4','4/4','6/8','9/8','12/8'];

        if (!in_array($signature, $allowed, true)) {
            return new Response('Signature invalide.', 400);
        }

        $original = $audio->getClientOriginalName();
        $title = trim((string)$request->request->get('title', ''))
            ?: pathinfo($original, PATHINFO_FILENAME);
        $artist = trim((string)$request->request->get('artist', ''));

        $sha = hash_file('sha256', $audio->getPathname());
        if ($sha === false) {
            return new Response('Impossible de calculer SHA-256.', 500);
        }

        $songId = $db->createSong($title, $artist, $original, $sha);

        $projectDir = (string)$this->getParameter('kernel.project_dir');
        $audioDir = $projectDir.DIRECTORY_SEPARATOR.'public'.DIRECTORY_SEPARATOR.'benchmark-audio';

        if (!is_dir($audioDir)) {
            mkdir($audioDir, 0777, true);
        }

        $ext = strtolower(pathinfo($original, PATHINFO_EXTENSION));
        $allowedExt = ['mp3','wav','flac','ogg','oga','m4a','mp4','aac'];
        if (!in_array($ext, $allowedExt, true)) {
            $ext = 'bin';
        }

        $placeholder = $audioDir.DIRECTORY_SEPARATOR.'pending-'.$songId.'.'.$ext;

        $audio->move($audioDir, basename($placeholder));

        $runId = $db->createRun($songId, $signature, $placeholder);
        $final = $audioDir.DIRECTORY_SEPARATOR.'run-'.$runId.'.'.$ext;

        rename($placeholder, $final);

        $db->pdo()
            ->prepare('UPDATE benchmark_runs SET input_path=? WHERE id=?')
            ->execute([$final, $runId]);

        try {
            $launcher->launch($runId, $final, $signature);
        } catch (\Throwable $e) {
            return new Response(
                'Analyse en erreur : '.htmlspecialchars($e->getMessage(), ENT_QUOTES),
                500
            );
        }

        return new RedirectResponse(
            $this->generateUrl('bench_view', ['id' => $runId])
        );
    }

    #[Route('/run/{id<\\d+>}', name: 'bench_view', methods: ['GET'])]
    public function view(int $id, Database $db): Response
    {
        $run = $db->run($id);

        if (!$run) {
            throw $this->createNotFoundException();
        }

        $audioAvailable = is_file((string)$run['input_path']);
        $audioUrl = $audioAvailable
            ? '/benchmark-audio/'.rawurlencode(basename((string)$run['input_path']))
            : null;

        return $this->render('benchmark/view.html.twig', [
            'run' => $run,
            'algorithms' => $db->algorithms($id),
            'review' => $db->runReview($id),
            'audio_available' => $audioAvailable,
            'audio_url' => $audioUrl,
        ]);
    }

    #[Route('/run/{id<\\d+>}/review', name: 'bench_review', methods: ['POST'])]
    public function review(int $id, Request $request, Database $db): Response
    {
        $run = $db->run($id);

        if (!$run) {
            throw $this->createNotFoundException();
        }

        $approved = $request->request->all('approved');
        $reference = trim((string)$request->request->get('reference', 'Riffstation'));
        $comment = trim((string)$request->request->get('comment', ''));

        $db->saveAlgorithmApprovals(
            $id,
            is_array($approved) ? $approved : [],
            $reference,
            $comment
        );

        return new RedirectResponse(
            $this->generateUrl('bench_view', ['id' => $id])
        );
    }




    #[Route('/run/{id<\d+>}/delete', name: 'bench_delete', methods: ['POST'])]
    public function delete(int $id, Database $db): Response
    {
        $deleted = $db->deleteSongByRunId($id);

        if ($deleted === null) {
            throw $this->createNotFoundException();
        }

        foreach ($deleted['audio_paths'] as $audioPath) {
            if (is_string($audioPath) && $audioPath !== '' && is_file($audioPath)) {
                @unlink($audioPath);
            }
        }

        $projectDir = (string)$this->getParameter('kernel.project_dir');
        $resultsDir = $projectDir.DIRECTORY_SEPARATOR.'results';

        foreach ($deleted['run_ids'] as $runId) {
            foreach (glob($resultsDir.DIRECTORY_SEPARATOR.sprintf('run-%06d-*', $runId)) ?: [] as $dir) {
                $this->removeTree($dir);
            }
        }

        return new RedirectResponse($this->generateUrl('bench_index'));
    }

    private function removeTree(string $path): void
    {
        if (!is_dir($path)) {
            return;
        }

        $items = scandir($path);
        if ($items === false) {
            return;
        }

        foreach ($items as $item) {
            if ($item === '.' || $item === '..') {
                continue;
            }

            $child = $path.DIRECTORY_SEPARATOR.$item;

            if (is_dir($child)) {
                $this->removeTree($child);
            } else {
                @unlink($child);
            }
        }

        @rmdir($path);
    }

}
