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
}
