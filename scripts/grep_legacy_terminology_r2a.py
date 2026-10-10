from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERN = re.compile(
    r"\b(?:ADN|DNA|Chromosome|chromosome|Genome|genome|Gene|gene|Genes|genes|Région|région|Region|region)\b"
)
SUFFIXES = {".php", ".py", ".twig", ".json", ".md", ".yaml", ".yml"}

rows = []
for p in ROOT.rglob("*"):
    if not p.is_file() or ".git" in p.parts or "vendor" in p.parts:
        continue
    if p.suffix.lower() not in SUFFIXES:
        continue
    try:
        text = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    for number, line in enumerate(text.splitlines(), start=1):
        if PATTERN.search(line):
            rows.append((p.relative_to(ROOT).as_posix(), number, line.strip()))

out = ROOT / "TERMINOLOGY_GREP_R2A_AFTER.txt"
out.write_text(
    "\n".join(f"{p}:{n}:{line}" for p, n, line in rows) + ("\n" if rows else ""),
    encoding="utf-8",
)

print("TERMINOLOGY_GREP_R2A_OK")
print(f"remaining_occurrences={len(rows)}")
print(f"report={out}")
