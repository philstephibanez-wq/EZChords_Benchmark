from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERN = re.compile(
    r"\b(?:ADN|DNA|Chromosome|chromosome|Genome|genome|Gene|gene|Genes|genes|"
    r"Région|région|Region|region)\b"
)
SUFFIXES = {".php", ".py", ".twig", ".json", ".md", ".yaml", ".yml", ".ps1"}

ALLOWED_ROOTS = (
    "src/",
    "templates/",
    "python/",
    "scripts/",
    "tests/",
    "config/",
    "contracts/",
    "presets/",
    "adn/",
)
EXCLUDED_PREFIXES = (
    "vendor/",
    "var/",
    "data/",
    ".git/",
    ".venv/",
    "venv/",
    "node_modules/",
)
EXCLUDED_NAMES = {
    "TERMINOLOGY_GREP_R2A_AFTER.txt",
}

def tracked_files() -> set[str]:
    cp = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        line.strip().replace("\\", "/")
        for line in cp.stdout.splitlines()
        if line.strip()
    }

files = []
for rel in sorted(tracked_files()):
    if rel in EXCLUDED_NAMES:
        continue
    if rel.startswith(EXCLUDED_PREFIXES):
        continue
    if not rel.startswith(ALLOWED_ROOTS):
        continue
    p = ROOT / rel
    if not p.is_file() or p.suffix.lower() not in SUFFIXES:
        continue
    files.append((rel, p))

rows = []
by_file: dict[str, int] = {}
for rel, p in files:
    try:
        text = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    for number, line in enumerate(text.splitlines(), start=1):
        if PATTERN.search(line):
            rows.append((rel, number, line.strip()))
            by_file[rel] = by_file.get(rel, 0) + 1

out = ROOT / "TERMINOLOGY_GREP_R2A_AFTER.txt"
out.write_text(
    "\n".join(f"{p}:{n}:{line}" for p,n,line in rows)
    + ("\n" if rows else ""),
    encoding="utf-8",
)

print("TERMINOLOGY_GREP_R2A_SCOPED_OK")
print(f"files_scanned={len(files)}")
print(f"files_with_legacy_terms={len(by_file)}")
print(f"remaining_occurrences={len(rows)}")
print(f"report={out}")
if by_file:
    print("top_files:")
    for path,count in sorted(by_file.items(), key=lambda x:(-x[1],x[0]))[:30]:
        print(f"  {count:4d}  {path}")
