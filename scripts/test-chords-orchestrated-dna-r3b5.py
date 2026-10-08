from __future__ import annotations
import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
entry=(ROOT/"analysis"/"worker_entrypoint.py").read_text(encoding="utf-8")
worker=(ROOT/"python"/"worker.py").read_text(encoding="utf-8")
engine=(ROOT/"python"/"engine.py").read_text(encoding="utf-8")

ast.parse(entry); ast.parse(worker); ast.parse(engine)

assert 'ALLOWED_KINDS = {"benchmark", "chords_scientific"}' in entry
assert '--selection-request' in entry
assert 'selection_request_outside_lab_runtime' in entry
assert '--selection-request' in worker
assert 'ezstudio.chords.selection.v1' in worker
assert 'experiment_inputs=experiment_inputs' in worker
assert 'def make_selected_mix' in engine
assert '_selected_by_input_role' in engine
assert '"chord_input"' in engine
assert '"no_chord_evidence"' in engine
assert 'selected_stem_hash_mismatch' in engine
assert 'selected_no_chord_hash_mismatch' in engine
assert 'E_positive_harmonic_support_selected' in engine
assert 'metric_algorithms_modified": False' in engine
for name in (
    "Beat This downbeat","Percussive onset","Bass CQT",
    "Rhythm + Bass","Harmonic novelty","R41-like fusion",
):
    assert name in engine, name
print("EZSTUDIO_CHORDS_ORCHESTRATED_DNA_R3B5_PY_CONTRACT_OK")
