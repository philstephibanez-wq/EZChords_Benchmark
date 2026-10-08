from __future__ import annotations

from pathlib import Path
import os
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "src" / "Service" / "Database.php"
source = PATH.read_text(encoding="utf-8-sig")

if "queueScientificStemsJob(" in source:
    print("EZSTUDIO_UNIFIED_LAB_QUEUE_R3B6_DATABASE_ALREADY_MIGRATED")
    raise SystemExit(0)

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)

old_schema = '''CREATE TABLE IF NOT EXISTS analysis_jobs (
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
);'''

new_schema = '''CREATE TABLE IF NOT EXISTS analysis_jobs (
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
);'''
source = replace_once(source, old_schema, new_schema, "analysis_jobs_schema")

old_benchmark_insert = '''        $stmt = $this->pdo()->prepare(
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
        ]);'''

new_benchmark_insert = '''        $stmt = $this->pdo()->prepare(
            'INSERT INTO analysis_jobs(
                run_id,scientific_run_id,song_id,source_path,
                kind,status,progress,request_json,error,created_at,updated_at
             ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
             ON CONFLICT(run_id,kind)
             DO UPDATE SET
                song_id=excluded.song_id,
                source_path=excluded.source_path,
                status=excluded.status,
                progress=excluded.progress,
                request_json=excluded.request_json,
                error=NULL,
                updated_at=excluded.updated_at'
        );
        $stmt->execute([
            $runId,
            null,
            (int)$run['song_id'],
            $audioPath,
            'benchmark',
            'queued',
            0,
            json_encode($request, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
            null,
            $now,
            $now,
        ]);'''
source = replace_once(source, old_benchmark_insert, new_benchmark_insert, "benchmark_insert")

anchor = "\n\n    public function queueScientificChordsJob("
stems_method = '''
    public function queueScientificStemsJob(
        int $scientificRunId,
        int $songId,
        string $sourcePath,
        string $audioHash,
        string $storageRoot,
        bool $force,
        string $engineProfile,
        ?int $parentJobId = null
    ): int {
        if ($scientificRunId <= 0) {
            throw new \\InvalidArgumentException('scientific_run_id_required');
        }
        if ($songId <= 0) {
            throw new \\InvalidArgumentException('song_id_required');
        }
        if (!is_file($sourcePath)) {
            throw new \\RuntimeException('stems_source_missing');
        }

        $request = [
            'scientific_run_id' => $scientificRunId,
            'audio_hash' => $audioHash,
            'storage_root' => $storageRoot,
            'force' => $force,
            'engine_profile' => $engineProfile,
            'parent_job_id' => $parentJobId,
            'output_contract' => 'ezstudio.stems.v1',
        ];
        $now = gmdate('c');

        $stmt = $this->pdo()->prepare(
            'INSERT INTO analysis_jobs(
                run_id,scientific_run_id,song_id,source_path,
                kind,status,progress,request_json,error,created_at,updated_at
             ) VALUES(NULL,?,?,?,?,?,?,?,?,?,?)'
        );
        $stmt->execute([
            $scientificRunId,
            $songId,
            $sourcePath,
            'stems',
            'queued',
            0,
            json_encode($request, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
            null,
            $now,
            $now,
        ]);

        return (int)$this->pdo()->lastInsertId();
    }

'''
if source.count(anchor) != 1:
    raise RuntimeError("stems_method_anchor_missing_or_ambiguous")
source = source.replace(anchor, "\n\n" + stems_method + "    public function queueScientificChordsJob(", 1)

old_chords_insert = '''        $stmt = $this->pdo()->prepare(
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
        ]);'''

new_chords_insert = '''        $stmt = $this->pdo()->prepare(
            'INSERT INTO analysis_jobs(
                run_id,scientific_run_id,song_id,source_path,
                kind,status,progress,request_json,error,created_at,updated_at
             ) VALUES(?,?,?,?,?,?,?,?,?,?,?)'
        );
        $stmt->execute([
            $benchmarkRunId,
            $scientificRunId,
            (int)$run['song_id'],
            (string)$run['input_path'],
            'chords_scientific',
            'queued',
            0,
            json_encode($request, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
            null,
            $now,
            $now,
        ]);'''
source = replace_once(source, old_chords_insert, new_chords_insert, "chords_insert")

old_queue = '''        $stmt = $this->pdo()->prepare(
            "SELECT j.id,j.kind,j.status,j.progress,j.run_id,
                    r.song_id,s.title,s.artist
             FROM analysis_jobs j
             JOIN benchmark_runs r ON r.id=j.run_id
             JOIN songs s ON s.id=r.song_id
             WHERE j.status='queued'
             ORDER BY j.created_at ASC,j.id ASC
             LIMIT ?"
        );'''

new_queue = '''        $stmt = $this->pdo()->prepare(
            "SELECT j.id,j.kind,j.status,j.progress,j.run_id,
                    j.scientific_run_id,j.song_id,s.title,s.artist
             FROM analysis_jobs j
             JOIN songs s ON s.id=j.song_id
             WHERE j.status='queued'
             ORDER BY j.created_at ASC,j.id ASC
             LIMIT ?"
        );'''
source = replace_once(source, old_queue, new_queue, "analysis_queue")

old_analysis_job = '''        $stmt = $this->pdo()->prepare(
            'SELECT j.*,r.song_id,r.input_path,r.requested_signature,
                    s.title,s.artist,s.audio_sha256
             FROM analysis_jobs j
             JOIN benchmark_runs r ON r.id=j.run_id
             JOIN songs s ON s.id=r.song_id
             WHERE j.id=?'
        );'''

new_analysis_job = '''        $stmt = $this->pdo()->prepare(
            'SELECT j.*,r.requested_signature,
                    s.title,s.artist,s.audio_sha256
             FROM analysis_jobs j
             LEFT JOIN benchmark_runs r ON r.id=j.run_id
             JOIN songs s ON s.id=j.song_id
             WHERE j.id=?'
        );'''
source = replace_once(source, old_analysis_job, new_analysis_job, "analysis_job")

old_claim = '''            $pdo->prepare(
                "UPDATE benchmark_runs
                 SET status='running',progress=1,updated_at=?,error=NULL
                 WHERE id=?"
            )->execute([$now, (int)$row['run_id']]);'''

new_claim = '''            if ($row['run_id'] !== null) {
                $pdo->prepare(
                    "UPDATE benchmark_runs
                     SET status='running',progress=1,updated_at=?,error=NULL
                     WHERE id=?"
                )->execute([$now, (int)$row['run_id']]);
            }'''
source = replace_once(source, old_claim, new_claim, "claim_benchmark_update")

source = replace_once(
    source,
    "'source' => (string)$job['input_path'],",
    "'source' => (string)$job['source_path'],",
    "analysis_context_source"
)

old_progress = '''        $this->pdo()->prepare(
            "UPDATE benchmark_runs SET progress=?,updated_at=? WHERE id=?"
        )->execute([$progress, $now, (int)$job['run_id']]);'''

new_progress = '''        if ($job['run_id'] !== null) {
            $this->pdo()->prepare(
                "UPDATE benchmark_runs SET progress=?,updated_at=? WHERE id=?"
            )->execute([$progress, $now, (int)$job['run_id']]);
        }'''
source = replace_once(source, old_progress, new_progress, "progress_benchmark_update")

old_complete = '''        $run = $this->run((int)$job['run_id']);
        if ($run === null || (string)$run['status'] !== 'done') {
            throw new \\RuntimeException('benchmark_run_not_done');
        }

        $this->pdo()->prepare('''

new_complete = '''        if ((string)$job['kind'] !== 'stems') {
            $run = $this->run((int)$job['run_id']);
            if ($run === null || (string)$run['status'] !== 'done') {
                throw new \\RuntimeException('benchmark_run_not_done');
            }
        }

        $this->pdo()->prepare('''
source = replace_once(source, old_complete, new_complete, "complete_semantics")

old_fail = '''        $run = $this->run((int)$job['run_id']);
        if ($run !== null && (string)$run['status'] !== 'done') {
            $this->pdo()->prepare(
                "UPDATE benchmark_runs
                 SET status='error',error=?,updated_at=?
                 WHERE id=?"
            )->execute([$message, $now, (int)$job['run_id']]);
        }'''

new_fail = '''        if ($job['run_id'] !== null) {
            $run = $this->run((int)$job['run_id']);
            if ($run !== null && (string)$run['status'] !== 'done') {
                $this->pdo()->prepare(
                    "UPDATE benchmark_runs
                     SET status='error',error=?,updated_at=?
                     WHERE id=?"
                )->execute([$message, $now, (int)$job['run_id']]);
            }
        }'''
source = replace_once(source, old_fail, new_fail, "fail_semantics")

anchor2 = "\n    public function analysisJob(int $id): ?array\n"
helper = '''    public function analysisJobsForSongKind(int $songId, string $kind): array
    {
        $stmt = $this->pdo()->prepare(
            'SELECT j.*,s.title,s.artist,s.audio_sha256
             FROM analysis_jobs j
             JOIN songs s ON s.id=j.song_id
             WHERE j.song_id=? AND j.kind=?
             ORDER BY j.id DESC'
        );
        $stmt->execute([$songId, $kind]);
        return $stmt->fetchAll();
    }

'''
if source.count(anchor2) != 1:
    raise RuntimeError("analysisJobsForSongKind_anchor_missing_or_ambiguous")
source = source.replace(anchor2, "\n" + helper + "    public function analysisJob(int $id): ?array\n", 1)

fd, tmp_name = tempfile.mkstemp(prefix="Database.php.", suffix=".tmp", dir=str(PATH.parent))
os.close(fd)
tmp = Path(tmp_name)
try:
    tmp.write_text(source, encoding="utf-8")
    os.replace(tmp, PATH)
finally:
    tmp.unlink(missing_ok=True)

print("EZSTUDIO_UNIFIED_LAB_QUEUE_R3B6_DATABASE_SOURCE_OK")
