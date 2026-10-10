<?php
namespace App\Service;

/** @deprecated Compatibility alias; use PresetRegistry. */
class GenomeRegistry extends PresetRegistry
{
    public function captureRunGenome(int $runId, string $region, array $manifest): array
    {
        return $this->captureRunPreset($runId, $region, $manifest);
    }

    public function genomeForRun(int $runId): ?array
    {
        return $this->presetForRun($runId);
    }

    public function regionRevision(int $id): array
    {
        return $this->phaseRevision($id);
    }

    public function promoteRegionRevision(int $id): array
    {
        return $this->promotePhaseRevision($id);
    }

    public function rejectRegionRevision(int $id): void
    {
        $this->rejectPhaseRevision($id);
    }

    public function diffRegionRevisions(int $fromId, int $toId): array
    {
        return $this->diffPhaseRevisions($fromId, $toId);
    }
}
