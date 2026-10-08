from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def insert_before(path: Path, anchor: str, block: str, marker: str) -> None:
    text = path.read_text(encoding="utf-8")
    if marker in text:
        return
    if anchor not in text:
        raise RuntimeError(f"{path}: anchor absent")
    path.write_text(
        text.replace(anchor, block + anchor, 1),
        encoding="utf-8",
        newline="\n",
    )

def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"{path}: replacement anchor absent")
    path.write_text(
        text.replace(old, new, 1),
        encoding="utf-8",
        newline="\n",
    )

def patch_database() -> None:
    p = ROOT / "src" / "Service" / "Database.php"
    block = r"""
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

"""
    insert_before(
        p,
        "    public function allRuns(): array\n",
        block,
        "public function allSongs(): array",
    )

def patch_controller() -> None:
    p = ROOT / "src" / "Controller" / "LabController.php"

    replace_once(
        p,
        "use Symfony\\Component\\HttpFoundation\\BinaryFileResponse;\n"
        "use Symfony\\Component\\HttpFoundation\\Response;\n",
        "use Symfony\\Component\\HttpFoundation\\BinaryFileResponse;\n"
        "use Symfony\\Component\\HttpFoundation\\Request;\n"
        "use Symfony\\Component\\HttpFoundation\\Response;\n",
    )

    start = "    #[Route('/', name: 'lab_index', methods: ['GET'])]\n"
    end = "    #[Route('/lab/run/{id<\\d+>}', name: 'lab_run', methods: ['GET'])]\n"

    text = p.read_text(encoding="utf-8")
    if "Request $request, Database $db" in text:
        return
    if start not in text or end not in text:
        raise RuntimeError(f"{p}: index method anchors absent")

    before, rest = text.split(start, 1)
    _old, after = rest.split(end, 1)

    new_method = r"""    #[Route('/', name: 'lab_index', methods: ['GET'])]
    public function index(Request $request, Database $db): Response
    {
        $songs = $db->allSongs();

        $requestedSongId = filter_var(
            $request->query->get('song'),
            FILTER_VALIDATE_INT,
            ['options' => ['min_range' => 1]],
        );

        $selectedSong = null;
        if ($requestedSongId !== false && $requestedSongId !== null) {
            $selectedSong = $db->song((int)$requestedSongId);
        }
        if ($selectedSong === null && $songs !== []) {
            $selectedSong = $db->song((int)$songs[0]['id']);
        }

        $workbenchRuns = [];
        $latestRun = null;

        if ($selectedSong !== null) {
            $latestRun = $db->latestRunForSong((int)$selectedSong['id']);

            foreach ($db->runsForSong((int)$selectedSong['id']) as $row) {
                $result = !empty($row['result_json'])
                    ? json_decode((string)$row['result_json'], true)
                    : null;

                $stems = is_array($result)
                    ? ($result['no_chord_benchmark']['stems'] ?? null)
                    : null;

                $workbenchRuns[] = [
                    'row' => $row,
                    'stems_ready' => is_array($stems) && !empty($stems['available']),
                    'chords_ready' => (string)($row['status'] ?? '') === 'done',
                    'no_chord_ready' => is_array($result)
                        && !empty($result['no_chord_benchmark']['active_variant']),
                    'lyrics_ready' => false,
                    'engine_version' => is_array($result)
                        ? ($result['engine_version'] ?? $row['engine_version'])
                        : $row['engine_version'],
                ];
            }
        }

        return $this->render('lab/index.html.twig', [
            'songs' => $songs,
            'selected_song' => $selectedSong,
            'latest_run' => $latestRun,
            'runs' => $workbenchRuns,
            'scores' => $db->globalScores(),
        ]);
    }

"""
    p.write_text(
        before + new_method + end + after,
        encoding="utf-8",
        newline="\n",
    )

def main() -> int:
    patch_database()
    patch_controller()
    print("EZSTUDIO_WORKBENCH_R3A1_MIGRATION_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
