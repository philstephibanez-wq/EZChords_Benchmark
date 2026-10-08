from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "scripts" / "migrate-workbench-r3a.py").read_text(encoding="utf-8")

assert 'newline="\\\\n"' not in src
assert 'newline="\\n"' in src
assert "EZSTUDIO_WORKBENCH_R3A1_MIGRATION_OK" in src

print("EZSTUDIO_WORKBENCH_R3A1_MIGRATION_CONTRACT_OK")
