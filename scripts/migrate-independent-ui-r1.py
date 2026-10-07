from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(f"Required file absent: {path}")
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def require(text: str, needle: str, label: str, path: Path) -> None:
    if needle not in text:
        raise RuntimeError(f"{path}: final contract absent: {label}")


def forbid(text: str, needle: str, label: str, path: Path) -> None:
    if needle in text:
        raise RuntimeError(f"{path}: forbidden legacy contract remains: {label}")


def migrate_engine(path: Path) -> None:
    text = read(path)

    # Clean baseline -> autonomous defaults. Already-migrated files are left intact.
    if "DEFAULT_EZSTUDIO_STEMS_SCRIPT" not in text:
        legacy = (
            '# EZScore is READ-ONLY from this benchmark.\n'
            'DEFAULT_EZSCORE_STEMS_SCRIPT = Path(r"H:\\EZScore\\analysis\\stems_only.py")\n'
            'DEFAULT_STEMS_CACHE_ROOT = Path(r"H:\\temp\\EZChords_Benchmark\\stems")'
        )
        target = (
            '# EZStudio_lab owns its STEMS pipeline and runtime storage.\n'
            'DEFAULT_EZSTUDIO_STEMS_SCRIPT = Path(__file__).resolve().parent / "ezstudio" / "pipeline" / "stems" / "runner.py"\n'
            'DEFAULT_STEMS_CACHE_ROOT = Path(r"H:\\temp\\EZStudio_lab\\stems")'
        )
        if legacy not in text:
            raise RuntimeError(f"{path}: unable to migrate STEMS defaults")
        text = text.replace(legacy, target, 1)

    replacements = {
        "def ensure_ezscore_stems(": "def ensure_ezstudio_stems(",
        'os.getenv("EZCHORDS_EZSCORE_STEMS_SCRIPT", str(DEFAULT_EZSCORE_STEMS_SCRIPT))':
            'os.getenv("EZSTUDIO_STEMS_SCRIPT", str(DEFAULT_EZSTUDIO_STEMS_SCRIPT))',
        'os.getenv("EZCHORDS_STEMS_CACHE_ROOT", str(DEFAULT_STEMS_CACHE_ROOT))':
            'os.getenv("EZSTUDIO_STEMS_CACHE_ROOT", str(DEFAULT_STEMS_CACHE_ROOT))',
        'script EZScore absent:': 'script EZStudio_lab absent:',
        'stems: appel READ-ONLY du script EZScore; sortie=': 'stems: pipeline autonome EZStudio_lab; sortie=',
        'stems: cache benchmark réutilisé ': 'stems: cache EZStudio_lab réutilisé ',
        '"source": "EZScore/analysis/stems_only.py"':
            '"source": "EZStudio_lab/python/ezstudio/pipeline/stems/runner.py"',
        '"read_only_ezscore": True': '"ezstudio_autonomous": True',
        'ensure_ezscore_stems(audio, work, log)': 'ensure_ezstudio_stems(audio, work, log)',
        '"ezscore_read_only": True': '"ezstudio_autonomous": True',
        '"ezscore_modified": False': '"ezscore_runtime_dependency": False',
        'print("EZSCORE_READ_ONLY_CONTRACT_OK")': 'print("EZSTUDIO_AUTONOMY_CONTRACT_OK")',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    # Documentation inside the function: replace legacy wording without relying
    # on exact slash escaping or whitespace.
    text = text.replace("READ-ONLY contract toward H:\\\\EZScore:", "EZStudio_lab autonomous STEMS contract:")
    text = text.replace("- never writes under EZScore;", "- no EZScore runtime dependency;")
    text = text.replace("- invokes its canonical stems_only.py only;", "- invokes EZStudio_lab own canonical STEMS runner;")
    text = text.replace(
        "- all generated data is redirected to H:\\\\temp\\\\EZChords_Benchmark\\\\stems.",
        "- generated data lives under H:\\\\temp\\\\EZStudio_lab\\\\stems.",
    )

    write(path, text)
    final = read(path)
    require(final, "DEFAULT_EZSTUDIO_STEMS_SCRIPT", "autonomous STEMS script", path)
    require(final, "def ensure_ezstudio_stems(", "autonomous STEMS function", path)
    require(final, "EZSTUDIO_STEMS_CACHE_ROOT", "autonomous STEMS cache env", path)
    require(final, "EZStudio_lab/python/ezstudio/pipeline/stems/runner.py", "autonomous STEMS source", path)
    forbid(final, r"H:\EZScore", "EZScore runtime path", path)
    forbid(final, "DEFAULT_EZSCORE_STEMS_SCRIPT", "legacy STEMS script symbol", path)
    forbid(final, "ensure_ezscore_stems", "legacy STEMS function", path)
    forbid(final, "EZCHORDS_EZSCORE_STEMS_SCRIPT", "legacy STEMS env", path)
    forbid(final, "EZChords_Benchmark", "legacy benchmark runtime identity", path)


def migrate_observability(path: Path) -> None:
    text = read(path)
    replacements = {
        r'H:\temp\EZChords_Benchmark\observability': r'H:\temp\EZStudio_lab\observability',
        r'H:\temp\EZChords_Benchmark\exports': r'H:\temp\EZStudio_lab\exports',
        'DEFAULT_MONGO_DB = "ezchords_benchmark"': 'DEFAULT_MONGO_DB = "ezstudio_lab"',
        'EZCHORDS_MONGO_URI': 'EZSTUDIO_MONGO_URI',
        'EZCHORDS_MONGO_DB': 'EZSTUDIO_MONGO_DB',
        'EZCHORDS_OBSERVABILITY_ROOT': 'EZSTUDIO_OBSERVABILITY_ROOT',
        'EZCHORDS_EXPORT_ROOT': 'EZSTUDIO_EXPORT_ROOT',
        '"ezscore_read_only": True': '"ezstudio_autonomous": True',
        '"ezscore_modified": False': '"ezscore_runtime_dependency": False',
        'EZChords_Run_': 'EZStudio_Run_',
        'V10_EZSCORE_READ_ONLY_CONTRACT_OK': 'V10_EZSTUDIO_AUTONOMY_CONTRACT_OK',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    write(path, text)
    final = read(path)
    require(final, r'H:\temp\EZStudio_lab\observability', "EZStudio observability path", path)
    require(final, 'DEFAULT_MONGO_DB = "ezstudio_lab"', "EZStudio Mongo DB", path)
    forbid(final, "EZChords_Benchmark", "legacy observability identity", path)


def migrate_launcher(path: Path) -> None:
    text = read(path).replace("EZChords_Benchmark", "EZStudio_lab")
    write(path, text)
    final = read(path)
    require(final, "EZStudio_lab", "EZStudio dependency root", path)
    forbid(final, "EZChords_Benchmark", "legacy launcher identity", path)


def migrate_controller(path: Path) -> None:
    text = read(path)
    # Root route may already have been moved by an interrupted R1 application.
    text = text.replace(
        "#[Route('/', name: 'bench_index', methods: ['GET'])]",
        "#[Route('/legacy', name: 'bench_index', methods: ['GET'])]",
    )
    # Deliberately replace only the identity token. This handles PHP sources
    # containing either H:\\temp... or H:\temp... without escaping assumptions.
    text = text.replace("EZChords_Benchmark", "EZStudio_lab")
    write(path, text)
    final = read(path)
    require(final, "#[Route('/legacy', name: 'bench_index'", "legacy index route", path)
    require(final, "EZStudio_lab", "EZStudio cache identity", path)
    forbid(final, "EZChords_Benchmark", "legacy controller identity", path)


def main() -> int:
    migrate_engine(ROOT / "python" / "engine.py")
    migrate_observability(ROOT / "python" / "observability.py")
    migrate_launcher(ROOT / "src" / "Service" / "BenchmarkLauncher.php")
    migrate_controller(ROOT / "src" / "Controller" / "BenchmarkController.php")

    print("EZSTUDIO_INDEPENDENT_SOURCE_MIGRATION_OK")
    print("EZSTUDIO_PARTIAL_APPLY_RESUME_OK")
    print("EZSTUDIO_IDEMPOTENT_MIGRATION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
