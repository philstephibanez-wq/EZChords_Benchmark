<?php
declare(strict_types=1);

$root = dirname(__DIR__);
$dbPath = $root.DIRECTORY_SEPARATOR.'data'.DIRECTORY_SEPARATOR.'benchmark.sqlite';
$pdo = new PDO('sqlite:'.$dbPath);
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
$pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

$columns = [];
foreach ($pdo->query("PRAGMA table_info(analysis_jobs)")->fetchAll() as $row) {
    $columns[(string)$row['name']] = $row;
}

if (isset($columns['scientific_run_id'], $columns['song_id'], $columns['source_path'])
    && (int)($columns['run_id']['notnull'] ?? 0) === 0
) {
    echo "EZSTUDIO_ANALYSIS_JOBS_R3B6_SCHEMA_ALREADY_OK\n";
    exit(0);
}

$pdo->exec('PRAGMA foreign_keys=OFF');
try {
    $pdo->beginTransaction();

    $pdo->exec(
        "CREATE TABLE analysis_jobs_r3b6 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            scientific_run_id INTEGER,
            song_id INTEGER NOT NULL,
            source_path TEXT NOT NULL,
            kind TEXT NOT NULL,
            status TEXT NOT NULL,
            progress INTEGER NOT NULL DEFAULT 0,
            request_json TEXT NOT NULL,
            error TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(run_id, kind),
            FOREIGN KEY(run_id) REFERENCES benchmark_runs(id) ON DELETE CASCADE,
            FOREIGN KEY(song_id) REFERENCES songs(id) ON DELETE CASCADE
        )"
    );

    $pdo->exec(
        "INSERT INTO analysis_jobs_r3b6(
            id,run_id,scientific_run_id,song_id,source_path,
            kind,status,progress,request_json,error,created_at,updated_at
         )
         SELECT
            j.id,j.run_id,NULL,r.song_id,r.input_path,
            j.kind,j.status,j.progress,j.request_json,j.error,j.created_at,j.updated_at
         FROM analysis_jobs j
         JOIN benchmark_runs r ON r.id=j.run_id"
    );

    $pdo->exec("DROP TABLE analysis_jobs");
    $pdo->exec("ALTER TABLE analysis_jobs_r3b6 RENAME TO analysis_jobs");
    $pdo->exec(
        "CREATE INDEX IF NOT EXISTS idx_analysis_jobs_status
         ON analysis_jobs(status, created_at, id)"
    );

    $pdo->commit();
} catch (Throwable $e) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }
    throw $e;
} finally {
    $pdo->exec('PRAGMA foreign_keys=ON');
}

echo "EZSTUDIO_ANALYSIS_JOBS_R3B6_SCHEMA_OK\n";
