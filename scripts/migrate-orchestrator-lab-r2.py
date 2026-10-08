from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"{path}: migration anchor absent")
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


def patch_database() -> None:
    p = ROOT / "src" / "Service" / "Database.php"

    replace_once(
        p,
        "CREATE TABLE IF NOT EXISTS run_logs (\n"
        "    id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "    run_id INTEGER NOT NULL,\n"
        "    created_at TEXT NOT NULL,\n"
        "    level TEXT NOT NULL,\n"
        "    message TEXT NOT NULL,\n"
        "    FOREIGN KEY(run_id) REFERENCES benchmark_runs(id) ON DELETE CASCADE\n"
        ");\n"
        "SQL;\n",
        "CREATE TABLE IF NOT EXISTS run_logs (\n"
        "    id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "    run_id INTEGER NOT NULL,\n"
        "    created_at TEXT NOT NULL,\n"
        "    level TEXT NOT NULL,\n"
        "    message TEXT NOT NULL,\n"
        "    FOREIGN KEY(run_id) REFERENCES benchmark_runs(id) ON DELETE CASCADE\n"
        ");\n"
        "\n"
        "CREATE TABLE IF NOT EXISTS analysis_jobs (\n"
        "    id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "    run_id INTEGER NOT NULL,\n"
        "    kind TEXT NOT NULL,\n"
        "    status TEXT NOT NULL,\n"
        "    progress INTEGER NOT NULL DEFAULT 0,\n"
        "    request_json TEXT NOT NULL,\n"
        "    error TEXT,\n"
        "    created_at TEXT NOT NULL,\n"
        "    updated_at TEXT NOT NULL,\n"
        "    UNIQUE(run_id, kind),\n"
        "    FOREIGN KEY(run_id) REFERENCES benchmark_runs(id) ON DELETE CASCADE\n"
        ");\n"
        "CREATE INDEX IF NOT EXISTS idx_analysis_jobs_status\n"
        "ON analysis_jobs(status, created_at, id);\n"
        "SQL;\n",
    )

    anchor = "    public function exportData(): array\n"
    methods = r'''    public function queueAnalysisJob(
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

'''
    text = p.read_text(encoding="utf-8")
    if "public function queueAnalysisJob(" not in text:
        if anchor not in text:
            raise RuntimeError(f"{p}: methods anchor absent")
        p.write_text(text.replace(anchor, methods + anchor, 1), encoding="utf-8", newline="\n")


def patch_launcher() -> None:
    p = ROOT / "src" / "Service" / "BenchmarkLauncher.php"
    text = p.read_text(encoding="utf-8")
    start = "    public function launch(int $runId, string $audioPath, string $signature): void\n    {\n"
    marker = "\n    /**\n     * @param list<string> $workerArgs\n     */\n"
    if "queueAnalysisJob($runId, $audioPath, $signature)" in text:
        return
    if start not in text or marker not in text:
        raise RuntimeError(f"{p}: launch anchors absent")
    before, rest = text.split(start, 1)
    _old_body, after = rest.split(marker, 1)
    new_method = (
        start
        + "        // R2: the permanent EZS_orchestrator service is the only worker.\n"
        + "        // EZStudio_lab only persists a target-owned queued job here.\n"
        + "        $this->database->queueAnalysisJob($runId, $audioPath, $signature);\n"
        + "    }\n"
    )
    p.write_text(before + new_method + marker + after, encoding="utf-8", newline="\n")


def patch_worker() -> None:
    p = ROOT / "python" / "worker.py"

    replace_once(
        p,
        "    ap.add_argument(\"--keep-upload\", choices=[\"0\", \"1\"], default=\"0\")\n"
        "    a = ap.parse_args()\n",
        "    ap.add_argument(\"--keep-upload\", choices=[\"0\", \"1\"], default=\"0\")\n"
        "    ap.add_argument(\"--progress-file\", default=\"\")\n"
        "    a = ap.parse_args()\n",
    )

    replace_once(
        p,
        "    db = sqlite3.connect(a.db, timeout=60)\n",
        "    progress_file = Path(a.progress_file).resolve() if a.progress_file else None\n"
        "    last_progress = 0\n"
        "\n"
        "    def write_progress_file(percent: int, status: str = \"running\", error: str | None = None):\n"
        "        if progress_file is None:\n"
        "            return\n"
        "        progress_file.parent.mkdir(parents=True, exist_ok=True)\n"
        "        payload = {\"percent\": int(percent), \"status\": status}\n"
        "        if error:\n"
        "            payload[\"error\"] = str(error)\n"
        "        tmp = progress_file.with_suffix(progress_file.suffix + \".tmp\")\n"
        "        tmp.write_text(json.dumps(payload, ensure_ascii=False) + \"\\n\", encoding=\"utf-8\")\n"
        "        os.replace(tmp, progress_file)\n"
        "\n"
        "    db = sqlite3.connect(a.db, timeout=60)\n",
    )

    replace_once(
        p,
        "    def progress(p):\n"
        "        db.execute(\n"
        "            \"UPDATE benchmark_runs \"\n"
        "            \"SET progress=?,updated_at=datetime('now') WHERE id=?\",\n"
        "            (int(p), a.run_id),\n"
        "        )\n"
        "        db.commit()\n",
        "    def progress(p):\n"
        "        nonlocal last_progress\n"
        "        last_progress = max(0, min(100, int(p)))\n"
        "        db.execute(\n"
        "            \"UPDATE benchmark_runs \"\n"
        "            \"SET progress=?,updated_at=datetime('now') WHERE id=?\",\n"
        "            (last_progress, a.run_id),\n"
        "        )\n"
        "        db.commit()\n"
        "        write_progress_file(last_progress)\n",
    )

    replace_once(
        p,
        "        db.commit()\n"
        "        log(\"INFO\", \"analyse terminée\")\n",
        "        db.commit()\n"
        "        progress(100)\n"
        "        write_progress_file(100, \"completed\")\n"
        "        log(\"INFO\", \"analyse terminée\")\n",
    )

    replace_once(
        p,
        "        db.commit()\n"
        "        return 1\n"
        "    finally:\n",
        "        db.commit()\n"
        "        write_progress_file(last_progress, \"error\", f\"{type(e).__name__}: {e}\")\n"
        "        return 1\n"
        "    finally:\n",
    )


def main() -> int:
    patch_database()
    patch_launcher()
    patch_worker()
    print("EZSTUDIO_ORCHESTRATOR_LAB_R2_MIGRATION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
