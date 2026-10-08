<?php

namespace App\Controller;

use App\Service\DnaRegistry;
use App\Service\LabCatalog;
use App\Service\LabJobStore;
use App\Service\StemsDnaSync;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\File\UploadedFile;
use Symfony\Component\HttpFoundation\RedirectResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Attribute\Route;

final class StemsLabController extends AbstractController
{
    #[Route('/stems', name: 'lab_stems', methods: ['GET'])]
    public function index(
        Request $request,
        LabJobStore $jobs,
        LabCatalog $catalog,
        StemsDnaSync $sync,
    ): Response {
        $songId = filter_var(
            $request->query->get('song'),
            FILTER_VALIDATE_INT,
            ['options' => ['min_range' => 1]],
        );
        $song = $catalog->song(
            ($songId === false || $songId === null) ? null : (int)$songId
        );

        $songJobs = $song
            ? $jobs->jobsForAudioHash((string)$song['audio_sha256'])
            : [];
        $dnaRuns = $sync->syncMany($songJobs);

        return $this->render('lab/stems.html.twig', [
            'songs' => $catalog->songs(),
            'selected_song' => $song,
            'jobs' => $songJobs,
            'dna_runs' => $dnaRuns,
            'source_available' => $song ? $catalog->sourcePath($song) !== null : false,
        ]);
    }

    #[Route('/stems/analyze', name: 'lab_stems_analyze', methods: ['POST'])]
    public function analyze(
        Request $request,
        LabJobStore $jobs,
        LabCatalog $catalog,
        DnaRegistry $dna,
    ): Response {
        $songId = filter_var(
            $request->request->get('song'),
            FILTER_VALIDATE_INT,
            ['options' => ['min_range' => 1]],
        );
        if ($songId === false || $songId === null) {
            return new Response('Chanson invalide.', 400);
        }

        $song = $catalog->song((int)$songId);
        if ($song === null) {
            return new Response('Chanson introuvable.', 404);
        }

        $source = $catalog->sourcePath($song);
        if ($source === null) {
            return new Response(
                'Audio source indisponible : impossible de lancer STEMS.',
                409
            );
        }

        $force = $request->request->getBoolean('force', false);
        $engineProfile = trim((string)$request->request->get(
            'engine_profile',
            'canonical_roformer'
        ));
        if ($engineProfile === '') {
            $engineProfile = 'canonical_roformer';
        }

        $scientific = $dna->createRun(
            (int)$song['id'],
            'stems',
            ['name' => $engineProfile],
            [
                'audio_hash' => (string)$song['audio_sha256'],
                'force_reanalysis' => $force,
                'engine_profile' => $engineProfile,
                'output_contract' => 'ezstudio.stems.v1',
            ],
        );

        $previous = $jobs->jobsForAudioHash((string)$song['audio_sha256']);
        $parentJobId = $previous !== [] ? (int)$previous[0]['job_id'] : null;

        $jobId = $jobs->reserveId();
        $jobs->createStemsJob(
            $jobId,
            $source,
            (string)$song['audio_sha256'],
            (string)$song['title'],
            (string)$song['artist'],
            $force,
            (int)$song['id'],
            $engineProfile,
            $parentJobId,
            (int)$scientific['id'],
        );

        $dna->setAlias((int)$scientific['id'], 'lab_job', (string)$jobId);
        $dna->setLabel((int)$scientific['id'], 'audio_sha256', (string)$song['audio_sha256']);
        $dna->setLabel((int)$scientific['id'], 'technical_job_id', (string)$jobId);
        $dna->setState((int)$scientific['id'], 'queued');

        return new RedirectResponse(
            $this->generateUrl('lab_stems_job', ['id' => $jobId])
        );
    }

    /*
     * Legacy upload endpoint kept only for backwards compatibility.
     * It is not exposed by the STEMS business UI.
     */
    #[Route('/stems/run', name: 'lab_stems_run', methods: ['POST'])]
    public function create(Request $request, LabJobStore $jobs): Response
    {
        /** @var UploadedFile|null $audio */
        $audio = $request->files->get('audio');
        if (!$audio instanceof UploadedFile || !$audio->isValid()) {
            return new Response('Fichier audio invalide.', 400);
        }

        $original = $audio->getClientOriginalName();
        $title = trim((string)$request->request->get('title', ''))
            ?: pathinfo($original, PATHINFO_FILENAME);
        $artist = trim((string)$request->request->get('artist', ''));
        $hash = hash_file('sha256', $audio->getPathname());
        if ($hash === false) {
            return new Response('SHA-256 impossible.', 500);
        }

        $jobId = $jobs->reserveId();
        $uploadRoot = 'H:\temp\EZStudio_lab\uploads';
        if (
            !is_dir($uploadRoot)
            && !mkdir($uploadRoot, 0777, true)
            && !is_dir($uploadRoot)
        ) {
            return new Response('Dossier upload impossible.', 500);
        }

        $ext = strtolower(pathinfo($original, PATHINFO_EXTENSION));
        if (!in_array($ext, ['wav','mp3','flac','ogg','oga','m4a','aac','mp4'], true)) {
            $ext = 'bin';
        }

        $target = $uploadRoot.DIRECTORY_SEPARATOR.sprintf(
            'job-%08d.%s',
            $jobId,
            $ext
        );
        $audio->move($uploadRoot, basename($target));

        $jobs->createStemsJob(
            $jobId,
            $target,
            $hash,
            $title,
            $artist
        );

        return new RedirectResponse(
            $this->generateUrl('lab_stems_job', ['id' => $jobId])
        );
    }

    #[Route('/stems/job/{id<\d+>}', name: 'lab_stems_job', methods: ['GET'])]
    public function job(
        int $id,
        LabJobStore $jobs,
        StemsDnaSync $sync,
    ): Response {
        $job = $jobs->get($id);
        if ($job === null) {
            throw $this->createNotFoundException();
        }

        $dnaRun = $sync->sync($job);
        $manifest = null;
        $diagnostics = null;
        $workerLog = '';
        $result = is_array($job['result'] ?? null) ? $job['result'] : [];

        if (!empty($result['manifest']) && is_file((string)$result['manifest'])) {
            $manifest = json_decode(
                (string)file_get_contents((string)$result['manifest']),
                true
            );
        }

        if (!empty($result['diagnostics']) && is_file((string)$result['diagnostics'])) {
            $diagnostics = json_decode(
                (string)file_get_contents((string)$result['diagnostics']),
                true
            );
        }

        $storageRoot = (string)($job['paths']['storage_root'] ?? '');
        $logPath = $storageRoot !== ''
            ? $storageRoot.DIRECTORY_SEPARATOR.'worker.log'
            : '';

        if ($logPath !== '' && is_file($logPath)) {
            $workerLog = (string)file_get_contents($logPath);
            if (strlen($workerLog) > 100000) {
                $workerLog = substr($workerLog, -100000);
            }
        }

        return $this->render('lab/stems_job.html.twig', [
            'job' => $job,
            'dna_run' => $dnaRun,
            'manifest' => is_array($manifest) ? $manifest : null,
            'diagnostics' => is_array($diagnostics) ? $diagnostics : null,
            'worker_log' => $workerLog,
        ]);
    }
}
