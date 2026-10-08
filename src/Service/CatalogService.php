<?php

namespace App\Service;

use PDO;

final class CatalogService
{
    private const ITEMS = ['profile', 'stems', 'chords', 'lyrics'];

    public function __construct(private readonly Database $db) {}

    public function songs(): array
    {
        $rows = $this->db->pdo()->query(
            'SELECT id,title,artist,source_filename,audio_sha256,source_path,created_at
             FROM songs
             ORDER BY id DESC'
        )->fetchAll();

        $groups = [];
        foreach ($rows as $song) {
            $hash = trim((string)$song['audio_sha256']);
            $key = $hash !== '' ? $hash : 'song:'.(int)$song['id'];

            if (!isset($groups[$key])) {
                $groups[$key] = [
                    'id' => (int)$song['id'],
                    'title' => (string)$song['title'],
                    'artist' => (string)$song['artist'],
                    'source_filename' => (string)$song['source_filename'],
                    'audio_sha256' => $hash,
                    'created_at' => (string)$song['created_at'],
                    'song_ids' => [],
                ];
                foreach (self::ITEMS as $item) {
                    $groups[$key][$item] = $this->emptyState();
                }
            }

            $groups[$key]['song_ids'][] = (int)$song['id'];
        }

        foreach ($groups as &$group) {
            foreach (self::ITEMS as $item) {
                $group[$item] = $this->latestScientificState(
                    $group['song_ids'],
                    $item
                );
            }

            // Compatibility with historical benchmark CHORDS.
            if ($group['chords']['state'] === 'none') {
                $legacy = $this->latestBenchmarkState($group['song_ids']);
                if ($legacy !== null) {
                    $group['chords'] = $legacy;
                }
            }
        }
        unset($group);

        $out = array_values($groups);
        usort(
            $out,
            static fn(array $a, array $b): int =>
                strcasecmp($a['title'].' '.$a['artist'], $b['title'].' '.$b['artist'])
        );

        return $out;
    }

    public function deleteGroup(int $songId): array
    {
        $stmt = $this->db->pdo()->prepare(
            'SELECT id,title,artist,audio_sha256,source_path
             FROM songs WHERE id=?'
        );
        $stmt->execute([$songId]);
        $seed = $stmt->fetch();
        if (!$seed) {
            throw new \RuntimeException('catalog_song_not_found');
        }

        $hash = (string)$seed['audio_sha256'];
        $stmt = $this->db->pdo()->prepare(
            'SELECT id,title,artist,audio_sha256,source_path
             FROM songs WHERE audio_sha256=? ORDER BY id'
        );
        $stmt->execute([$hash]);
        $songs = $stmt->fetchAll();
        if ($songs === []) {
            throw new \RuntimeException('catalog_song_group_empty');
        }

        $songIds = array_map(
            static fn(array $row): int => (int)$row['id'],
            $songs
        );
        $marks = implode(',', array_fill(0, count($songIds), '?'));

        $this->db->cancelStaleAnalysisJobsForSongs($songIds, 60);
        $this->db->requestAnalysisCancellationForSongs($songIds);

        $deadline = microtime(true) + 30.0;
        do {
            $activeJobs = $this->db->activeOrCancellingAnalysisJobsForSongs($songIds);
            if ($activeJobs === []) {
                break;
            }
            usleep(200000);
        } while (microtime(true) < $deadline);

        $activeJobs = $this->db->activeOrCancellingAnalysisJobsForSongs($songIds);
        if ($activeJobs !== []) {
            $ids = implode(',', array_map(
                static fn(array $row): string => (string)$row['id'],
                $activeJobs
            ));
            throw new \RuntimeException(
                'catalog_song_cancel_timeout:jobs='.$ids
            );
        }

        $files = [];
        foreach ($songs as $song) {
            $path = trim((string)($song['source_path'] ?? ''));
            if ($path !== '') {
                $files[$path] = true;
            }
        }

        $benchmarkRunIds = [];
        $stmt = $this->db->pdo()->prepare(
            "SELECT id,input_path FROM benchmark_runs
             WHERE song_id IN ($marks)"
        );
        $this->bindIds($stmt, $songIds);
        $stmt->execute();
        foreach ($stmt->fetchAll() as $row) {
            $benchmarkRunIds[] = (int)$row['id'];
            $path = trim((string)($row['input_path'] ?? ''));
            if ($path !== '') {
                $files[$path] = true;
            }
        }

        $scientificRunIds = [];
        if ($this->tableExists('scientific_runs')) {
            $stmt = $this->db->pdo()->prepare(
                "SELECT id FROM scientific_runs WHERE song_id IN ($marks)"
            );
            $this->bindIds($stmt, $songIds);
            $stmt->execute();
            $scientificRunIds = array_map(
                static fn(array $row): int => (int)$row['id'],
                $stmt->fetchAll()
            );
        }

        if ($scientificRunIds !== []) {
            $runMarks = implode(',', array_fill(0, count($scientificRunIds), '?'));

            // Do not destroy a run that is still referenced by another song.
            $stmt = $this->db->pdo()->prepare(
                "SELECT COUNT(*)
                 FROM scientific_run_parents p
                 JOIN scientific_runs child ON child.id=p.child_run_id
                 WHERE p.parent_run_id IN ($runMarks)
                   AND child.song_id NOT IN ($marks)"
            );
            $i = 1;
            foreach ($scientificRunIds as $id) {
                $stmt->bindValue($i++, $id, PDO::PARAM_INT);
            }
            foreach ($songIds as $id) {
                $stmt->bindValue($i++, $id, PDO::PARAM_INT);
            }
            $stmt->execute();
            if ((int)$stmt->fetchColumn() > 0) {
                throw new \RuntimeException('catalog_song_has_external_child_runs');
            }

            $stmt = $this->db->pdo()->prepare(
                "SELECT COUNT(*)
                 FROM scientific_run_inputs i
                 JOIN scientific_runs consumer ON consumer.id=i.run_id
                 JOIN scientific_artifacts a ON a.artifact_id=i.artifact_id
                 WHERE a.run_id IN ($runMarks)
                   AND consumer.song_id NOT IN ($marks)"
            );
            $i = 1;
            foreach ($scientificRunIds as $id) {
                $stmt->bindValue($i++, $id, PDO::PARAM_INT);
            }
            foreach ($songIds as $id) {
                $stmt->bindValue($i++, $id, PDO::PARAM_INT);
            }
            $stmt->execute();
            if ((int)$stmt->fetchColumn() > 0) {
                throw new \RuntimeException('catalog_song_artifacts_still_used');
            }

            $stmt = $this->db->pdo()->prepare(
                "SELECT path FROM scientific_artifacts
                 WHERE run_id IN ($runMarks)"
            );
            $this->bindIds($stmt, $scientificRunIds);
            $stmt->execute();
            foreach ($stmt->fetchAll() as $row) {
                $path = trim((string)($row['path'] ?? ''));
                if ($path !== '') {
                    $files[$path] = true;
                }
            }
        }

        $jobIds = [];
        $stmt = $this->db->pdo()->prepare(
            "SELECT id FROM analysis_jobs WHERE song_id IN ($marks)"
        );
        $this->bindIds($stmt, $songIds);
        $stmt->execute();
        $jobIds = array_map(
            static fn(array $row): int => (int)$row['id'],
            $stmt->fetchAll()
        );

        $pdo = $this->db->pdo();
        $pdo->beginTransaction();
        try {
            if ($scientificRunIds !== []) {
                $runMarks = implode(',', array_fill(0, count($scientificRunIds), '?'));

                $stmt = $pdo->prepare(
                    "DELETE FROM scientific_run_inputs
                     WHERE run_id IN ($runMarks)
                        OR artifact_id IN (
                            SELECT artifact_id FROM scientific_artifacts
                            WHERE run_id IN ($runMarks)
                        )"
                );
                $i = 1;
                foreach ($scientificRunIds as $id) {
                    $stmt->bindValue($i++, $id, PDO::PARAM_INT);
                }
                foreach ($scientificRunIds as $id) {
                    $stmt->bindValue($i++, $id, PDO::PARAM_INT);
                }
                $stmt->execute();

                $stmt = $pdo->prepare(
                    "DELETE FROM scientific_run_parents
                     WHERE child_run_id IN ($runMarks)
                        OR parent_run_id IN ($runMarks)"
                );
                $i = 1;
                foreach ($scientificRunIds as $id) {
                    $stmt->bindValue($i++, $id, PDO::PARAM_INT);
                }
                foreach ($scientificRunIds as $id) {
                    $stmt->bindValue($i++, $id, PDO::PARAM_INT);
                }
                $stmt->execute();
            }

            $stmt = $pdo->prepare("DELETE FROM songs WHERE id IN ($marks)");
            $this->bindIds($stmt, $songIds);
            $stmt->execute();

            $pdo->commit();
        } catch (\Throwable $e) {
            if ($pdo->inTransaction()) {
                $pdo->rollBack();
            }
            throw $e;
        }

        foreach (array_keys($files) as $path) {
            if (is_file($path)) {
                @unlink($path);
            }
        }

        $runtimeRoot = rtrim(
            (string)(getenv('EZSTUDIO_RUNTIME_ROOT') ?: 'H:\\temp\\EZStudio_lab'),
            '\\/'
        );

        if ($hash !== '') {
            $this->removeTree($runtimeRoot.DIRECTORY_SEPARATOR.'stems'.DIRECTORY_SEPARATOR.$hash);
            $this->removeTree($runtimeRoot.DIRECTORY_SEPARATOR.'profile'.DIRECTORY_SEPARATOR.$hash);
        }

        foreach ($jobIds as $jobId) {
            $this->removeTree(
                $runtimeRoot.DIRECTORY_SEPARATOR.'jobs'.DIRECTORY_SEPARATOR.(string)$jobId
            );
        }

        $projectRoot = dirname(__DIR__, 2);
        foreach ($benchmarkRunIds as $runId) {
            foreach (
                glob(
                    $projectRoot.DIRECTORY_SEPARATOR.'results'
                    .DIRECTORY_SEPARATOR.sprintf('run-%06d-*', $runId)
                ) ?: []
                as $path
            ) {
                $this->removeTree($path);
            }
        }

        return [
            'song_ids' => $songIds,
            'audio_sha256' => $hash,
            'title' => (string)$seed['title'],
            'artist' => (string)$seed['artist'],
        ];
    }

    private function latestScientificState(array $songIds, string $item): array
    {
        if (!$this->tableExists('scientific_runs') || $songIds === []) {
            return $this->emptyState();
        }

        $marks = implode(',', array_fill(0, count($songIds), '?'));
        $stmt = $this->db->pdo()->prepare(
            "SELECT id,public_id,state,created_at
             FROM scientific_runs
             WHERE song_id IN ($marks) AND item=?
             ORDER BY id DESC LIMIT 1"
        );
        $i = 1;
        foreach ($songIds as $id) {
            $stmt->bindValue($i++, $id, PDO::PARAM_INT);
        }
        $stmt->bindValue($i, $item, PDO::PARAM_STR);
        $stmt->execute();
        $run = $stmt->fetch();

        if (!$run) {
            return $this->emptyState();
        }

        $progress = null;
        if ($this->tableExists('scientific_run_labels')) {
            $stmt = $this->db->pdo()->prepare(
                "SELECT value FROM scientific_run_labels
                 WHERE run_id=? AND label='progress'"
            );
            $stmt->execute([(int)$run['id']]);
            $value = $stmt->fetchColumn();
            if ($value !== false && is_numeric($value)) {
                $progress = max(0, min(100, (int)$value));
            }
        }

        return [
            'state' => (string)$run['state'],
            'progress' => $progress,
            'run_id' => (int)$run['id'],
            'public_id' => (string)$run['public_id'],
            'created_at' => (string)$run['created_at'],
            'legacy' => false,
        ];
    }

    private function latestBenchmarkState(array $songIds): ?array
    {
        if ($songIds === []) {
            return null;
        }

        $marks = implode(',', array_fill(0, count($songIds), '?'));
        $stmt = $this->db->pdo()->prepare(
            "SELECT id,status,progress,created_at
             FROM benchmark_runs
             WHERE song_id IN ($marks)
             ORDER BY id DESC LIMIT 1"
        );
        $this->bindIds($stmt, $songIds);
        $stmt->execute();
        $run = $stmt->fetch();

        if (!$run) {
            return null;
        }

        $state = match ((string)$run['status']) {
            'done' => 'done',
            'error' => 'error',
            default => (string)$run['status'],
        };

        return [
            'state' => $state,
            'progress' => (int)$run['progress'],
            'run_id' => (int)$run['id'],
            'public_id' => 'legacy-'.(int)$run['id'],
            'created_at' => (string)$run['created_at'],
            'legacy' => true,
        ];
    }

    private function emptyState(): array
    {
        return [
            'state' => 'none',
            'progress' => null,
            'run_id' => null,
            'public_id' => null,
            'created_at' => null,
            'legacy' => false,
        ];
    }

    private function tableExists(string $name): bool
    {
        $stmt = $this->db->pdo()->prepare(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?"
        );
        $stmt->execute([$name]);
        return (int)$stmt->fetchColumn() > 0;
    }

    private function bindIds(\PDOStatement $stmt, array $ids): void
    {
        foreach (array_values($ids) as $i => $id) {
            $stmt->bindValue($i + 1, (int)$id, PDO::PARAM_INT);
        }
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
