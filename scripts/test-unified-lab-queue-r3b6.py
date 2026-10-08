from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
entry = (ROOT / "analysis" / "worker_entrypoint.py").read_text(encoding="utf-8")
ast.parse(entry)

assert 'ALLOWED_KINDS = {"benchmark", "stems", "chords_scientific"}' in entry
assert 'stems_runner_missing' in entry
assert '--audio-hash' in entry
assert '--storage-root' in entry
assert 'source_outside_lab_root' in entry
assert 'stems_storage_outside_lab_runtime' in entry

controller = (ROOT / "src" / "Controller" / "StemsLabController.php").read_text(encoding="utf-8")
assert "LabJobStore" not in controller
assert "StemsDnaSync" not in controller
assert "HTTP_GONE" in controller

engine = (ROOT / "python" / "engine.py").read_text(encoding="utf-8")
for name in (
    "Beat This downbeat",
    "Percussive onset",
    "Bass CQT",
    "Rhythm + Bass",
    "Harmonic novelty",
    "R41-like fusion",
):
    assert name in engine

print("EZSTUDIO_UNIFIED_LAB_QUEUE_R3B6_PY_CONTRACT_OK")
