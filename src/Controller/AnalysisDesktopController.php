<?php

declare(strict_types=1);

namespace App\Controller;

use App\Service\Database;
use App\Service\ChordsDnaExecutionService;
use App\Service\LabAnalysisTokenGuard;
use App\Service\StemsDnaExecutionService;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Attribute\Route;

#[Route('/internal/analysis/desktop')]
final class AnalysisDesktopController extends AbstractController
{
    public function __construct(
        private readonly LabAnalysisTokenGuard $guard,
        private readonly Database $db,
        private readonly ChordsDnaExecutionService $chordsDna,
        private readonly StemsDnaExecutionService $stemsDna,
    ) {}

    #[Route('/hello', name: 'lab_internal_analysis_hello', methods: ['POST'])]
    public function hello(Request $request): JsonResponse
    {
        $this->guard->assertAuthorized($request);
        return $this->json([
            'schema_version' => 'ezstudio.analysis-desktop.v1',
            'target' => 'lab',
            'server_time' => gmdate('c'),
            'state' => ['ok' => true],
            'commands' => [],
        ]);
    }

    #[Route('/heartbeat', name: 'lab_internal_analysis_heartbeat', methods: ['POST'])]
    public function heartbeat(Request $request): JsonResponse
    {
        $this->guard->assertAuthorized($request);
        return $this->json([
            'schema_version' => 'ezstudio.analysis-desktop.v1',
            'target' => 'lab',
            'server_time' => gmdate('c'),
            'state' => ['ok' => true],
            'commands' => [],
        ]);
    }

    #[Route('/jobs/queue', name: 'lab_internal_analysis_queue', methods: ['GET'])]
    public function queue(Request $request): JsonResponse
    {
        $this->guard->assertAuthorized($request);
        return $this->json([
            'schema_version' => 'ezstudio.analysis-desktop.v1',
            'jobs' => $this->db->analysisQueue(),
        ]);
    }

    #[Route('/jobs/claim', name: 'lab_internal_analysis_claim', methods: ['POST'])]
    public function claim(Request $request): Response
    {
        $this->guard->assertAuthorized($request);
        $job = $this->db->claimNextAnalysisJob();
        if ($job === null) {
            return new Response('', Response::HTTP_NO_CONTENT);
        }
        return $this->json($this->db->analysisJobContext((int)$job['id']));
    }

    #[Route('/jobs/{id<\d+>}/context', name: 'lab_internal_analysis_context', methods: ['GET'])]
    public function context(int $id, Request $request): JsonResponse
    {
        $this->guard->assertAuthorized($request);
        $job = $this->db->analysisJob($id);
        if ($job === null) {
            return $this->json(['error' => 'job_not_found'], 404);
        }
        return $this->json($this->db->analysisJobContext($id));
    }

    #[Route('/jobs/{id<\d+>}/progress', name: 'lab_internal_analysis_progress', methods: ['POST'])]
    public function progress(int $id, Request $request): JsonResponse
    {
        $this->guard->assertAuthorized($request);
        $payload = $request->toArray();
        $value = filter_var(
            $payload['progress'] ?? null,
            FILTER_VALIDATE_INT,
            ['options' => ['min_range' => 0, 'max_range' => 100]],
        );
        if ($value === false) {
            return $this->json(['error' => 'progress_must_be_0_100'], 422);
        }
        if (!$this->db->updateAnalysisJobProgress($id, (int)$value)) {
            return $this->json(['error' => 'job_not_running'], 409);
        }

        $this->stemsDna->progressFromJob($id, (int)$value);
        $this->chordsDna->progressFromJob($id, (int)$value);

        return $this->json([
            'job_id' => $id,
            'status' => 'running',
            'progress' => (int)$value,
        ]);
    }

    #[Route('/jobs/{id<\d+>}/complete', name: 'lab_internal_analysis_complete', methods: ['POST'])]
    public function complete(int $id, Request $request): JsonResponse
    {
        $this->guard->assertAuthorized($request);
        try {
            $this->db->completeAnalysisJob($id);
            $this->stemsDna->completeFromJob($id);
            $this->chordsDna->completeFromJob($id);
        } catch (\RuntimeException $e) {
            return $this->json(['error' => $e->getMessage()], 409);
        }

        return $this->json([
            'job_id' => $id,
            'status' => 'completed',
            'progress' => 100,
        ]);
    }

    #[Route('/jobs/{id<\d+>}/fail', name: 'lab_internal_analysis_fail', methods: ['POST'])]
    public function fail(int $id, Request $request): JsonResponse
    {
        $this->guard->assertAuthorized($request);
        $payload = $request->toArray();
        $error = trim((string)($payload['error'] ?? 'orchestrator_job_failed'));

        $this->db->failAnalysisJob($id, $error);
        $this->stemsDna->failFromJob($id, $error);
        $this->chordsDna->failFromJob($id, $error);

        return $this->json([
            'job_id' => $id,
            'status' => 'failed',
        ]);
    }
}
