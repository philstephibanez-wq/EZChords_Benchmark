from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

entrypoint = ROOT / "analysis" / "worker_entrypoint.py"
worker = ROOT / "python" / "worker.py"

assert entrypoint.is_file()
assert worker.is_file()

entry_src = entrypoint.read_text(encoding="utf-8")
worker_src = worker.read_text(encoding="utf-8")

ast.parse(entry_src, filename=str(entrypoint))
ast.parse(worker_src, filename=str(worker))

for needle in (
    'PROTOCOL = "ezscore.analysis-job.v2"',
    'ALLOWED_KIND = "benchmark"',
    'EZS_TARGET',
    'EZS_EXPECTED_ROOT',
    '"--job-file"',
    '"--progress-file"',
    'source_outside_lab_root',
    'database_outside_lab_root',
    'progress_outside_lab_runtime',
):
    assert needle in entry_src, needle

for needle in (
    'ap.add_argument("--progress-file", default="")',
    '"percent": int(percent)',
    'write_progress_file(last_progress)',
    'write_progress_file(100, "completed")',
):
    assert needle in worker_src, needle

print("EZSTUDIO_ORCHESTRATOR_LAB_R2_PYTHON_CONTRACT_OK")
