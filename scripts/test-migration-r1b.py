from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
MIGRATOR = PACKAGE / "scripts" / "migrate-independent-ui-r1.py"

ENGINE_CLEAN = r'''from pathlib import Path
# EZScore is READ-ONLY from this benchmark.
DEFAULT_EZSCORE_STEMS_SCRIPT = Path(r"H:\EZScore\analysis\stems_only.py")
DEFAULT_STEMS_CACHE_ROOT = Path(r"H:\temp\EZChords_Benchmark\stems")

def ensure_ezscore_stems(audio: Path, work: Path, log) -> dict:
    """
    READ-ONLY contract toward H:\\EZScore:
    - never writes under EZScore;
    - invokes its canonical stems_only.py only;
    - all generated data is redirected to H:\\temp\\EZChords_Benchmark\\stems.
    """
    script = Path(os.getenv("EZCHORDS_EZSCORE_STEMS_SCRIPT", str(DEFAULT_EZSCORE_STEMS_SCRIPT)))
    if not script.is_file():
        return {"available": False, "reason": f"script EZScore absent: {script}"}
    cache_root = Path(os.getenv("EZCHORDS_STEMS_CACHE_ROOT", str(DEFAULT_STEMS_CACHE_ROOT)))
    log("INFO", f"stems: appel READ-ONLY du script EZScore; sortie={cache_root}")
    log("INFO", f"stems: cache benchmark réutilisé {cache_root}")
    return {"source": "EZScore/analysis/stems_only.py", "read_only_ezscore": True}

def analyze(audio, work, log):
    stems_info = ensure_ezscore_stems(audio, work, log)
    return {"parameters": {"ezscore_read_only": True}, "contract": {"ezscore_modified": False}}

def self_test():
    print("EZSCORE_READ_ONLY_CONTRACT_OK")
'''

OBS_CLEAN = r'''from pathlib import Path
DEFAULT_ROOT = Path(r"H:\temp\EZChords_Benchmark\observability")
DEFAULT_EXPORT_ROOT = Path(r"H:\temp\EZChords_Benchmark\exports")
DEFAULT_MONGO_DB = "ezchords_benchmark"
def f():
    a = "EZCHORDS_MONGO_URI"
    b = "EZCHORDS_MONGO_DB"
    c = "EZCHORDS_OBSERVABILITY_ROOT"
    d = "EZCHORDS_EXPORT_ROOT"
    return {"ezscore_read_only": True, "ezscore_modified": False}, "EZChords_Run_000001", a+b+c+d
def self_test():
    print("V10_EZSCORE_READ_ONLY_CONTRACT_OK")
'''

LAUNCHER_CLEAN = r'''<?php
namespace App\Service;
final class BenchmarkLauncher {
    public function __construct(private readonly string $dependencyRoot = 'H:\\temp\\EZChords_Benchmark\\deps') {}
}
'''

CONTROLLER_CLEAN = r'''<?php
namespace App\Controller;
use Symfony\Component\Routing\Attribute\Route;
final class BenchmarkController {
    #[Route('/', name: 'bench_index', methods: ['GET'])]
    public function index(): void {}
    public function cached(): string {
        $cacheRoot = 'H:\\temp\\EZChords_Benchmark\\stems';
        return $cacheRoot;
    }
}
'''


def make_repo(root: Path) -> None:
    for rel, content in {
        "python/engine.py": ENGINE_CLEAN,
        "python/observability.py": OBS_CLEAN,
        "src/Service/BenchmarkLauncher.php": LAUNCHER_CLEAN,
        "src/Controller/BenchmarkController.php": CONTROLLER_CLEAN,
    }.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    dst = root / "scripts" / MIGRATOR.name
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MIGRATOR, dst)


def run(root: Path) -> None:
    p = subprocess.run([sys.executable, str(root / "scripts" / MIGRATOR.name)], cwd=root, text=True, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(p.stdout + "\n" + p.stderr)


def assert_final(root: Path) -> None:
    paths = [
        root / "python/engine.py",
        root / "python/observability.py",
        root / "src/Service/BenchmarkLauncher.php",
        root / "src/Controller/BenchmarkController.php",
    ]
    merged = "\n".join(p.read_text(encoding="utf-8") for p in paths)
    assert "EZChords_Benchmark" not in merged
    assert r"H:\EZScore" not in merged
    assert "DEFAULT_EZSCORE_STEMS_SCRIPT" not in merged
    assert "ensure_ezscore_stems" not in merged
    assert "DEFAULT_EZSTUDIO_STEMS_SCRIPT" in merged
    assert "ensure_ezstudio_stems" in merged
    assert "ezstudio_lab" in merged
    controller = (root / "src/Controller/BenchmarkController.php").read_text(encoding="utf-8")
    assert "#[Route('/legacy', name: 'bench_index'" in controller
    assert r"H:\\temp\\EZStudio_lab\\stems" in controller


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="ezstudio-r1b-") as td:
        clean = Path(td) / "clean"
        make_repo(clean)
        run(clean)
        assert_final(clean)
        print("R1B_CLEAN_MIGRATION_OK")

        # Second execution on already migrated state.
        run(clean)
        assert_final(clean)
        print("R1B_IDEMPOTENCE_OK")

        # Recreate the exact kind of interrupted state seen in R1: upstream
        # files migrated, controller route moved, but doubled-backslash cache
        # path still carries EZChords_Benchmark.
        partial = Path(td) / "partial"
        make_repo(partial)
        run(partial)
        ctrl = partial / "src/Controller/BenchmarkController.php"
        text = ctrl.read_text(encoding="utf-8")
        text = text.replace(r"H:\\temp\\EZStudio_lab\\stems", r"H:\\temp\\EZChords_Benchmark\\stems")
        ctrl.write_text(text, encoding="utf-8")
        run(partial)
        assert_final(partial)
        print("R1B_PARTIAL_RESUME_OK")

        # PHP syntax after migration for the fixture controller/launcher.
        for p in [partial / "src/Controller/BenchmarkController.php", partial / "src/Service/BenchmarkLauncher.php"]:
            proc = subprocess.run(["php", "-l", str(p)], text=True, capture_output=True)
            if proc.returncode != 0:
                raise RuntimeError(proc.stdout + proc.stderr)
        print("R1B_MIGRATED_PHP_LINT_OK")

    print("R1B_MIGRATION_TESTS_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
