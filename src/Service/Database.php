<?php
namespace App\Service;

use PDO;

final class Database
{
    private ?PDO $pdo = null;

    public function __construct(private readonly string $databasePath) {}

    public function pdo(): PDO
    {
        if ($this->pdo instanceof PDO) {
            return $this->pdo;
        }

        $dir = dirname($this->databasePath);
        if (!is_dir($dir)) {
            mkdir($dir, 0777, true);
        }

        $pdo = new PDO('sqlite:'.$this->databasePath);
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
        $pdo->exec('PRAGMA foreign_keys = ON');
        $pdo->exec('PRAGMA journal_mode = WAL');

        $this->pdo = $pdo;
        $this->ensureSchema();

        return $this->pdo;
    }

    public function path(): string
    {
        return $this->databasePath;
    }

    private function ensureSchema(): void
    {
        $sql = <<<'SQL'
CREATE TABLE IF NOT EXISTS songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    artist TEXT NOT NULL DEFAULT '',
    source_filename TEXT NOT NULL,
    audio_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_songs_sha ON songs(audio_sha256);

CREATE TABLE IF NOT EXISTS benchmark_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    song_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    requested_signature TEXT NOT NULL,
    detected_signature TEXT,
    tempo REAL,
    status TEXT NOT NULL,
    progress INTEGER NOT NULL DEFAULT 0,
    engine_version TEXT NOT NULL,
    input_path TEXT NOT NULL,
    error TEXT,
    result_json TEXT,
    FOREIGN KEY(song_id) REFERENCES songs(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_runs_song ON benchmark_runs(song_id);

CREATE TABLE IF NOT EXISTS algorithm_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    algorithm TEXT NOT NULL,
    phase INTEGER NOT NULL,
    score REAL NOT NULL,
    margin REAL NOT NULL,
    grid_json TEXT NOT NULL,
    UNIQUE(run_id, algorithm),
    FOREIGN KEY(run_id) REFERENCES benchmark_runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS judgements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL UNIQUE,
    selected_algorithm TEXT NOT NULL,
    selected_phase INTEGER NOT NULL,
    reference TEXT NOT NULL DEFAULT '',
    comment TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES benchmark_runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS run_reviews (
    run_id INTEGER PRIMARY KEY,
    reference TEXT NOT NULL DEFAULT '',
    comment TEXT NOT NULL DEFAULT '',
    reviewed_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES benchmark_runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS algorithm_reviews (
    run_id INTEGER NOT NULL,
    algorithm TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('approved','rejected')),
    reviewed_at TEXT NOT NULL,
    PRIMARY KEY(run_id, algorithm),
    FOREIGN KEY(run_id) REFERENCES benchmark_runs(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_algorithm_reviews_algorithm ON algorithm_reviews(algorithm);

CREATE TABLE IF NOT EXISTS run_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES benchmark_runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS analysis_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    kind TEXT NOT NULL,
    status TEXT NOT NULL,
    progress INTEGER NOT NULL DEFAULT 0,
    request_json TEXT NOT NULL,
    error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(run_id, kind),
    FOREIGN KEY(run_id) REFERENCES benchmark_runs(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_analysis_jobs_status
ON analysis_jobs(status, created_at, id);
SQL;

        $this->pdo->exec($sql);
    }

    public function allRuns(): array
    {
        $sql = 'SELECT r.*, s.title, s.artist, s.source_filename,
                       rr.reference AS review_reference,
                       rr.comment AS review_comment,
                       rr.reviewed_at
                FROM benchmark_runs r
                JOIN songs s ON s.id = r.song_id
                LEFT JOIN run_reviews rr ON rr.run_id = r.id
                ORDER BY r.id DESC';

        return $this->pdo()->query($sql)->fetchAll();
    }

    public function createSong(string $title, string $artist, string $filename, string $sha): int
    {
        $stmt = $this->pdo()->prepare(
            'INSERT INTO songs(title,artist,source_filename,audio_sha256,created_at)
             VALUES(?,?,?,?,?)'
        );
        $stmt->execute([$title, $artist, $filename, $sha, gmdate('c')]);

        return (int)$this->pdo()->lastInsertId();
    }

    public function createRun(int $songId, string $signature, string $inputPath): int
    {
        $now = gmdate('c');

        $stmt = $this->pdo()->prepare(
            'INSERT INTO benchmark_runs(
                song_id,created_at,updated_at,requested_signature,status,
                progress,engine_version,input_path
             ) VALUES(?,?,?,?,?,?,?,?)'
        );

        $stmt->execute([
            $songId,
            $now,
            $now,
            $signature,
            'running',
            0,
            'r6-app-v2',
            $inputPath,
        ]);

        return (int)$this->pdo()->lastInsertId();
    }

    public function run(int $id): ?array
    {
        $stmt = $this->pdo()->prepare(
            'SELECT r.*, s.title, s.artist, s.source_filename, s.audio_sha256
             FROM benchmark_runs r
             JOIN songs s ON s.id = r.song_id
             WHERE r.id=?'
        );

        $stmt->execute([$id]);
        $row = $stmt->fetch();

        return $row ?: null;
    }

    public function algorithms(int $runId): array
    {
        $stmt = $this->pdo()->prepare(
            'SELECT ar.*,
                    rv.status AS review_status
             FROM algorithm_results ar
             LEFT JOIN algorithm_reviews rv
               ON rv.run_id = ar.run_id
              AND rv.algorithm = ar.algorithm
             WHERE ar.run_id=?
             ORDER BY ar.id'
        );

        $stmt->execute([$runId]);
        $rows = $stmt->fetchAll();

        foreach ($rows as &$row) {
            $row['grid'] = json_decode($row['grid_json'], true) ?: [];
            $row['review_status'] = $row['review_status'] ?: 'unreviewed';
        }

        return $rows;
    }

    public function logs(int $runId, int $limit = 200): array
    {
        $stmt = $this->pdo()->prepare(
            'SELECT * FROM run_logs
             WHERE run_id=?
             ORDER BY id DESC
             LIMIT ?'
        );

        $stmt->bindValue(1, $runId, PDO::PARAM_INT);
        $stmt->bindValue(2, $limit, PDO::PARAM_INT);
        $stmt->execute();

        return array_reverse($stmt->fetchAll());
    }

    public function runReview(int $runId): ?array
    {
        $stmt = $this->pdo()->prepare(
            'SELECT * FROM run_reviews WHERE run_id=?'
        );
        $stmt->execute([$runId]);

        $row = $stmt->fetch();

        return $row ?: null;
    }

    public function saveAlgorithmApprovals(
        int $runId,
        array $approvedAlgorithms,
        string $reference,
        string $comment
    ): void {
        $this->pdo()->beginTransaction();

        try {
            $algorithms = $this->algorithms($runId);
            $approved = array_fill_keys(array_map('strval', $approvedAlgorithms), true);
            $now = gmdate('c');

            $upsertReview = $this->pdo()->prepare(
                'INSERT INTO algorithm_reviews(run_id,algorithm,status,reviewed_at)
                 VALUES(?,?,?,?)
                 ON CONFLICT(run_id,algorithm)
                 DO UPDATE SET
                    status=excluded.status,
                    reviewed_at=excluded.reviewed_at'
            );

            foreach ($algorithms as $algorithm) {
                $name = (string)$algorithm['algorithm'];
                $status = isset($approved[$name]) ? 'approved' : 'rejected';

                $upsertReview->execute([
                    $runId,
                    $name,
                    $status,
                    $now,
                ]);
            }

            $stmt = $this->pdo()->prepare(
                'INSERT INTO run_reviews(run_id,reference,comment,reviewed_at)
                 VALUES(?,?,?,?)
                 ON CONFLICT(run_id)
                 DO UPDATE SET
                    reference=excluded.reference,
                    comment=excluded.comment,
                    reviewed_at=excluded.reviewed_at'
            );

            $stmt->execute([
                $runId,
                $reference,
                $comment,
                $now,
            ]);

            $this->pdo()->commit();
        } catch (\Throwable $e) {
            $this->pdo()->rollBack();
            throw $e;
        }
    }

    public function deleteSongByRunId(int $runId): ?array
    {
        $run = $this->run($runId);

        if ($run === null) {
            return null;
        }

        $songId = (int)$run['song_id'];

        $stmt = $this->pdo()->prepare(
            'SELECT id, input_path FROM benchmark_runs WHERE song_id=? ORDER BY id'
        );
        $stmt->execute([$songId]);
        $runs = $stmt->fetchAll();

        $runIds = array_map(
            static fn(array $row): int => (int)$row['id'],
            $runs
        );

        $audioPaths = array_values(array_unique(array_filter(array_map(
            static fn(array $row): string => (string)$row['input_path'],
            $runs
        ))));

        $this->pdo()->beginTransaction();

        try {
            $delete = $this->pdo()->prepare('DELETE FROM songs WHERE id=?');
            $delete->execute([$songId]);
            $this->pdo()->commit();
        } catch (\Throwable $e) {
            $this->pdo()->rollBack();
            throw $e;
        }

        return [
            'song_id' => $songId,
            'run_ids' => $runIds,
            'audio_paths' => $audioPaths,
        ];
    }

    public function globalScores(): array
    {
        $sql = <<<'SQL'
SELECT
    ar.algorithm,
    COUNT(DISTINCT ar.run_id) AS total_runs,
    SUM(CASE WHEN rv.status='approved' THEN 1 ELSE 0 END) AS approved,
    SUM(CASE WHEN rv.status='rejected' THEN 1 ELSE 0 END) AS rejected,
    SUM(CASE WHEN rv.status IS NOT NULL THEN 1 ELSE 0 END) AS reviewed
FROM algorithm_results ar
JOIN benchmark_runs br ON br.id = ar.run_id AND br.status='done'
LEFT JOIN algorithm_reviews rv
  ON rv.run_id = ar.run_id
 AND rv.algorithm = ar.algorithm
GROUP BY ar.algorithm
ORDER BY ar.algorithm
SQL;

        $rows = $this->pdo()->query($sql)->fetchAll();

        foreach ($rows as &$row) {
            $reviewed = (int)$row['reviewed'];
            $approved = (int)$row['approved'];

            $row['score_percent'] = $reviewed > 0
                ? round(($approved / $reviewed) * 100.0, 1)
                : null;

            $row['unreviewed'] = (int)$row['total_runs'] - $reviewed;
        }

        usort(
            $rows,
            static function (array $a, array $b): int {
                $as = $a['score_percent'] ?? -1;
                $bs = $b['score_percent'] ?? -1;

                if ($as === $bs) {
                    return strcmp((string)$a['algorithm'], (string)$b['algorithm']);
                }

                return $bs <=> $as;
            }
        );

        return $rows;
    }

    public function reportRows(): array
    {
        $sql = <<<'SQL'
SELECT
    br.id AS run_id,
    s.title,
    s.artist,
    br.detected_signature,
    br.requested_signature,
    br.tempo,
    ar.algorithm,
    ar.phase,
    rv.status AS review_status,
    rr.reference,
    rr.comment,
    rr.reviewed_at
FROM benchmark_runs br
JOIN songs s ON s.id = br.song_id
JOIN algorithm_results ar ON ar.run_id = br.id
LEFT JOIN algorithm_reviews rv
  ON rv.run_id = ar.run_id
 AND rv.algorithm = ar.algorithm
LEFT JOIN run_reviews rr
  ON rr.run_id = br.id
WHERE br.status='done'
ORDER BY s.title COLLATE NOCASE, s.artist COLLATE NOCASE, ar.algorithm
SQL;

        $rows = $this->pdo()->query($sql)->fetchAll();

        foreach ($rows as &$row) {
            $row['review_status'] = $row['review_status'] ?: 'unreviewed';
        }

        return $rows;
    }

    public function queueAnalysisJob(
        int $runId,
        string $audioPath,
        string $signature
    ): int {
        $run = $this->run($runId);
        if ($run === null) {
            throw new \RuntimeException('run_not_found');
        }

        $request = [
            'run_id' => $runId,
            'database' => $this->path(),
            'signature' => $signature,
            'deps' => (string)(getenv('EZSTUDIO_DEP_ROOT') ?: 'H:\\temp\\EZStudio_lab\\deps'),
            'keep_upload' => ((string)(getenv('KEEP_UPLOADS') ?: '1')) !== '0',
            'audio_sha256' => (string)($run['audio_sha256'] ?? ''),
        ];
        $now = gmdate('c');

        $stmt = $this->pdo()->prepare(
            'INSERT INTO analysis_jobs(
                run_id,kind,status,progress,request_json,error,created_at,updated_at
             ) VALUES(?,?,?,?,?,?,?,?)
             ON CONFLICT(run_id,kind)
             DO UPDATE SET
                status=excluded.status,
                progress=excluded.progress,
                request_json=excluded.request_json,
                error=NULL,
                updated_at=excluded.updated_at'
        );
        $stmt->execute([
            $runId,
            'benchmark',
            'queued',
            0,
            json_encode($request, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
            null,
            $now,
            $now,
        ]);

        $select = $this->pdo()->prepare(
            "SELECT id FROM analysis_jobs WHERE run_id=? AND kind='benchmark'"
        );
        $select->execute([$runId]);
        $jobId = (int)$select->fetchColumn();

        $this->pdo()->prepare(
            "UPDATE benchmark_runs
             SET status='running',progress=0,error=NULL,updated_at=?
             WHERE id=?"
        )->execute([$now, $runId]);

        $this->pdo()->prepare(
            'INSERT INTO run_logs(run_id,created_at,level,message)
             VALUES(?,?,?,?)'
        )->execute([
            $runId,
            $now,
            'INFO',
            'job LAB queued for EZS_orchestrator: #'.$jobId,
        ]);

        return $jobId;
    }


    public function queueScientificChordsJob(
        int $benchmarkRunId,
        int $scientificRunId,
        string $selectionRequestPath,
        string $signature
    ): int {
        $run = $this->run($benchmarkRunId);
        if ($run === null) {
            throw new \RuntimeException('benchmark_run_not_found');
        }
        if ($scientificRunId <= 0) {
            throw new \InvalidArgumentException('scientific_run_id_required');
        }
        if (!is_file($selectionRequestPath)) {
            throw new \RuntimeException('selection_request_missing');
        }

        $request = [
            'run_id' => $benchmarkRunId,
            'scientific_run_id' => $scientificRunId,
            'database' => $this->path(),
            'signature' => $signature,
            'deps' => (string)(getenv('EZSTUDIO_DEP_ROOT') ?: 'H:\\temp\\EZStudio_lab\\deps'),
            'keep_upload' => true,
            'audio_sha256' => (string)($run['audio_sha256'] ?? ''),
            'selection_request' => $selectionRequestPath,
            'execution_contract' => 'ezstudio.chords.selection.v1',
        ];
        $now = gmdate('c');

        $stmt = $this->pdo()->prepare(
            'INSERT INTO analysis_jobs(
                run_id,kind,status,progress,request_json,error,created_at,updated_at
             ) VALUES(?,?,?,?,?,?,?,?)'
        );
        $stmt->execute([
            $benchmarkRunId,
            'chords_scientific',
            'queued',
            0,
            json_encode($request, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
            null,
            $now,
            $now,
        ]);
        $jobId = (int)$this->pdo()->lastInsertId();

        $this->pdo()->prepare(
            "UPDATE benchmark_runs
             SET status='running',progress=0,error=NULL,updated_at=?
             WHERE id=?"
        )->execute([$now, $benchmarkRunId]);

        $this->pdo()->prepare(
            'INSERT INTO run_logs(run_id,created_at,level,message)
             VALUES(?,?,?,?)'
        )->execute([
            $benchmarkRunId,
            $now,
            'INFO',
            'scientific CHORDS job queued for EZS_orchestrator: #'.$jobId
                .' ; scientific_run='.$scientificRunId,
        ]);

        return $jobId;
    }

    public function analysisQueue(int $limit = 100): array
    {
        $stmt = $this->pdo()->prepare(
            "SELECT j.id,j.kind,j.status,j.progress,j.run_id,
                    r.song_id,s.title,s.artist
             FROM analysis_jobs j
             JOIN benchmark_runs r ON r.id=j.run_id
             JOIN songs s ON s.id=r.song_id
             WHERE j.status='queued'
             ORDER BY j.created_at ASC,j.id ASC
             LIMIT ?"
        );
        $stmt->bindValue(1, max(1, min(500, $limit)), PDO::PARAM_INT);
        $stmt->execute();

        $rows = [];
        foreach ($stmt->fetchAll() as $row) {
            $rows[] = [
                'job_id' => (int)$row['id'],
                'kind' => (string)$row['kind'],
                'status' => (string)$row['status'],
                'progress' => (int)$row['progress'],
                'song_id' => (int)$row['song_id'],
                'title' => (string)$row['title'],
                'artist' => (string)$row['artist'],
                'resource_class' => 'gpu',
                'priority' => 50,
            ];
        }
        return $rows;
    }

    public function analysisJob(int $id): ?array
    {
        $stmt = $this->pdo()->prepare(
            'SELECT j.*,r.song_id,r.input_path,r.requested_signature,
                    s.title,s.artist,s.audio_sha256
             FROM analysis_jobs j
             JOIN benchmark_runs r ON r.id=j.run_id
             JOIN songs s ON s.id=r.song_id
             WHERE j.id=?'
        );
        $stmt->execute([$id]);
        $row = $stmt->fetch();
        return $row ?: null;
    }

    public function claimNextAnalysisJob(): ?array
    {
        $pdo = $this->pdo();
        $pdo->exec('BEGIN IMMEDIATE');
        try {
            $row = $pdo->query(
                "SELECT * FROM analysis_jobs
                 WHERE status='queued'
                 ORDER BY created_at ASC,id ASC
                 LIMIT 1"
            )->fetch();

            if (!$row) {
                $pdo->commit();
                return null;
            }

            $now = gmdate('c');
            $stmt = $pdo->prepare(
                "UPDATE analysis_jobs
                 SET status='running',progress=1,updated_at=?,error=NULL
                 WHERE id=? AND status='queued'"
            );
            $stmt->execute([$now, (int)$row['id']]);
            if ($stmt->rowCount() !== 1) {
                $pdo->rollBack();
                return null;
            }

            $pdo->prepare(
                "UPDATE benchmark_runs
                 SET status='running',progress=1,updated_at=?,error=NULL
                 WHERE id=?"
            )->execute([$now, (int)$row['run_id']]);

            $pdo->commit();
            return $this->analysisJob((int)$row['id']);
        } catch (\Throwable $e) {
            if ($pdo->inTransaction()) {
                $pdo->rollBack();
            }
            throw $e;
        }
    }

    public function analysisJobContext(int $id): array
    {
        $job = $this->analysisJob($id);
        if ($job === null) {
            throw new \RuntimeException('job_not_found');
        }

        $request = json_decode((string)$job['request_json'], true);
        if (!is_array($request)) {
            throw new \RuntimeException('invalid_job_request');
        }

        $runtimeRoot = rtrim(
            (string)(getenv('EZSTUDIO_RUNTIME_ROOT') ?: 'H:\\temp\\EZStudio_lab'),
            '\\/'
        );
        $progressFile = $runtimeRoot
            .DIRECTORY_SEPARATOR.'jobs'
            .DIRECTORY_SEPARATOR.(string)$id
            .DIRECTORY_SEPARATOR.'progress.json';

        return [
            'protocol' => 'ezscore.analysis-job.v2',
            'job_id' => (int)$job['id'],
            'kind' => (string)$job['kind'],
            'resource_class' => 'gpu',
            'priority' => 50,
            'song_id' => (int)$job['song_id'],
            'paths' => [
                'source' => (string)$job['input_path'],
                'progress_file' => $progressFile,
            ],
            'request' => $request,
            'song' => [
                'title' => (string)$job['title'],
                'artist' => (string)$job['artist'],
            ],
        ];
    }

    public function updateAnalysisJobProgress(int $id, int $progress): bool
    {
        if ($progress < 0 || $progress > 100) {
            throw new \InvalidArgumentException('progress_must_be_0_100');
        }

        $job = $this->analysisJob($id);
        if ($job === null || (string)$job['status'] !== 'running') {
            return false;
        }

        $now = gmdate('c');
        $this->pdo()->prepare(
            "UPDATE analysis_jobs SET progress=?,updated_at=? WHERE id=?"
        )->execute([$progress, $now, $id]);
        $this->pdo()->prepare(
            "UPDATE benchmark_runs SET progress=?,updated_at=? WHERE id=?"
        )->execute([$progress, $now, (int)$job['run_id']]);
        return true;
    }

    public function completeAnalysisJob(int $id): void
    {
        $job = $this->analysisJob($id);
        if ($job === null) {
            throw new \RuntimeException('job_not_found');
        }
        if ((string)$job['status'] !== 'running') {
            throw new \RuntimeException('job_not_running');
        }

        $run = $this->run((int)$job['run_id']);
        if ($run === null || (string)$run['status'] !== 'done') {
            throw new \RuntimeException('benchmark_run_not_done');
        }

        $this->pdo()->prepare(
            "UPDATE analysis_jobs
             SET status='completed',progress=100,error=NULL,updated_at=?
             WHERE id=?"
        )->execute([gmdate('c'), $id]);
    }

    public function failAnalysisJob(int $id, string $error): void
    {
        $job = $this->analysisJob($id);
        if ($job === null) {
            return;
        }

        $message = mb_substr(
            trim($error) !== '' ? trim($error) : 'orchestrator_job_failed',
            0,
            1000
        );
        $now = gmdate('c');

        $this->pdo()->prepare(
            "UPDATE analysis_jobs
             SET status='failed',error=?,updated_at=?
             WHERE id=?"
        )->execute([$message, $now, $id]);

        $run = $this->run((int)$job['run_id']);
        if ($run !== null && (string)$run['status'] !== 'done') {
            $this->pdo()->prepare(
                "UPDATE benchmark_runs
                 SET status='error',error=?,updated_at=?
                 WHERE id=?"
            )->execute([$message, $now, (int)$job['run_id']]);
        }
    }

    public function exportData(): array
    {
        $runs = $this->allRuns();

        foreach ($runs as &$run) {
            $runId = (int)$run['id'];
            $run['algorithms'] = $this->algorithms($runId);
            $run['review'] = $this->runReview($runId);

            if (!empty($run['result_json'])) {
                $run['result'] = json_decode((string)$run['result_json'], true);
            } else {
                $run['result'] = null;
            }

            unset($run['input_path'], $run['result_json']);
        }

        return [
            'schema_version' => 2,
            'exported_at' => gmdate('c'),
            'global_scores' => $this->globalScores(),
            'runs' => $runs,
        ];
    }

    public function allSongs(): array
    {
        $sql = "SELECT s.id,s.title,s.artist,s.source_filename,s.audio_sha256,s.created_at,
                       COUNT(r.id) AS run_count,
                       MAX(r.id) AS latest_run_id,
                       MAX(r.updated_at) AS latest_run_updated_at
                FROM songs s
                LEFT JOIN benchmark_runs r ON r.song_id=s.id
                GROUP BY s.id,s.title,s.artist,s.source_filename,s.audio_sha256,s.created_at
                ORDER BY s.title COLLATE NOCASE, s.artist COLLATE NOCASE, s.id";

        return $this->pdo()->query($sql)->fetchAll();
    }

    public function song(int $id): ?array
    {
        $stmt = $this->pdo()->prepare(
            "SELECT id,title,artist,source_filename,audio_sha256,created_at
             FROM songs
             WHERE id=?"
        );
        $stmt->execute([$id]);
        $row = $stmt->fetch();

        return $row ?: null;
    }

    public function runsForSong(int $songId): array
    {
        $stmt = $this->pdo()->prepare(
            "SELECT r.*, s.title, s.artist, s.source_filename, s.audio_sha256,
                    rr.reference AS review_reference,
                    rr.comment AS review_comment,
                    rr.reviewed_at
             FROM benchmark_runs r
             JOIN songs s ON s.id=r.song_id
             LEFT JOIN run_reviews rr ON rr.run_id=r.id
             WHERE r.song_id=?
             ORDER BY r.id DESC"
        );
        $stmt->execute([$songId]);

        return $stmt->fetchAll();
    }

    public function latestRunForSong(int $songId): ?array
    {
        $stmt = $this->pdo()->prepare(
            "SELECT r.*, s.title, s.artist, s.source_filename, s.audio_sha256
             FROM benchmark_runs r
             JOIN songs s ON s.id=r.song_id
             WHERE r.song_id=?
             ORDER BY r.id DESC
             LIMIT 1"
        );
        $stmt->execute([$songId]);
        $row = $stmt->fetch();

        return $row ?: null;
    }

}
