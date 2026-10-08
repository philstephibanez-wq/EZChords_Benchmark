from __future__ import annotations
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

DB_METHODS = r"""
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

NEW_INDEX = r"""    #[Route('/', name: 'lab_index', methods: ['GET'])]
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

def patch_database_text(text: str) -> str:
    if "public function allSongs(): array" in text:
        return text
    pos = text.rfind("\n}")
    if pos < 0:
        raise RuntimeError("Database.php: final class brace not found")
    return text[:pos] + "\n" + DB_METHODS.rstrip() + "\n" + text[pos:]

def patch_controller_text(text: str) -> str:
    if "use Symfony\\Component\\HttpFoundation\\Request;" not in text:
        use_pat = re.compile(
            r"(use\s+Symfony\\Component\\HttpFoundation\\BinaryFileResponse;\s*)",
            re.M,
        )
        text, count = use_pat.subn(
            r"\1use Symfony\\Component\\HttpFoundation\\Request;\n",
            text,
            count=1,
        )
        if count != 1:
            raise RuntimeError("LabController.php: cannot insert Request import")

    if "public function index(Request $request, Database $db): Response" in text:
        return text

    pattern = re.compile(
        r"(?ms)^[ \t]*#\[Route\('/'\s*,\s*name:\s*'lab_index'.*?\)\]\s*"
        r"public function index\s*\([^)]*\)\s*:\s*Response\s*\{.*?"
        r"(?=^[ \t]*#\[Route\('/lab/run/\{id<\\\\d\+>\}')",
    )
    match = pattern.search(text)
    if not match:
        # More tolerant fallback: next Route('/lab/run/
        pattern = re.compile(
            r"(?ms)^[ \t]*#\[Route\('/'\s*,\s*name:\s*'lab_index'.*?\)\]\s*"
            r"public function index\s*\([^)]*\)\s*:\s*Response\s*\{.*?"
            r"(?=^[ \t]*#\[Route\('/lab/run/)",
        )
        match = pattern.search(text)
    if not match:
        raise RuntimeError("LabController.php: lab_index method block not found")

    return text[:match.start()] + NEW_INDEX + text[match.end():]

def patch_file(path: Path, transform) -> None:
    original = path.read_text(encoding="utf-8")
    patched = transform(original)
    if patched != original:
        path.write_text(patched, encoding="utf-8", newline="\n")

def main() -> int:
    patch_file(ROOT / "src" / "Service" / "Database.php", patch_database_text)
    patch_file(ROOT / "src" / "Controller" / "LabController.php", patch_controller_text)
    print("EZSTUDIO_WORKBENCH_R3A2_MIGRATION_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
