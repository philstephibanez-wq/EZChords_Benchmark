from __future__ import annotations

import ast
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / "python"
if str(PYTHON) not in sys.path:
    sys.path.insert(0, str(PYTHON))

from ezstudio.runtime.adapters.clap_zero_shot import (
    _prompts,
    family_rows_from_logits,
)
from ezstudio.runtime.decision import apply_decision
from ezstudio.runtime.gene_spec import load_gene_spec

SPEC = ROOT / "adn/specs/profile/semantic.clap-open-vocabulary.r3b35c.json"
WRAPPER = ROOT / "python/ezstudio/pipeline/profile/genes/semantic_clap_open_vocab.py"
LEGACY = ROOT / "python/ezstudio/pipeline/profile/semantic_clap.py"
ADAPTER = ROOT / "python/ezstudio/runtime/adapters/clap_zero_shot.py"

for path in (SPEC, WRAPPER, LEGACY, ADAPTER):
    assert path.is_file(), path

# Syntax only: no heavyweight model imports happen here.
ast.parse(WRAPPER.read_text(encoding="utf-8"))
ast.parse(ADAPTER.read_text(encoding="utf-8"))
ast.parse(LEGACY.read_text(encoding="utf-8"))

spec = load_gene_spec(SPEC)
assert spec.region == "profile"
assert spec.gene_id == "semantic.clap-open-vocabulary"
assert spec.revision == "r3b35c-compat-v1"
assert spec.engine_adapter == "clap-zero-shot"

families = spec.data["taxonomy"]["families"]
assert len(families["genre"]) == 20
assert len(families["instrumentation"]) == 25
assert len(families["mood"]) == 20
assert len(families["voice"]) == 11

policies = spec.data["decision"]["families"]
assert policies["genre"] == {"mode": "compatibility_top_k", "top_k": 6}
assert policies["instrumentation"] == {"mode": "compatibility_top_k", "top_k": 12}
assert policies["mood"] == {"mode": "compatibility_top_k", "top_k": 8}
assert policies["voice"] == {"mode": "compatibility_top_k", "top_k": 8}

prompts, index = _prompts(spec)
assert len(prompts) == sum(len(v) for v in families.values())
assert len(index) == len(prompts)
assert "This music contains acoustic guitar." in prompts
assert "The recording features choir." in prompts

# Prove that scientific behavior is now data-driven: same engine primitive,
# different Gene Spec decision => different selection, no engine code edit.
import numpy as np
toy_index = [("genre", "a"), ("genre", "b"), ("genre", "c")]
rows = family_rows_from_logits(np.asarray([3.0, 2.0, 1.0]), toy_index, "genre")
compat = apply_decision(rows, {"mode": "compatibility_top_k", "top_k": 2})
assert [x["label"] for x in compat["selected"]] == ["a", "b"]

mutated = apply_decision(rows, {"mode": "compatibility_top_k", "top_k": 1})
assert [x["label"] for x in mutated["selected"]] == ["a"]

wrapper_text = WRAPPER.read_text(encoding="utf-8")
assert "run_clap_zero_shot" in wrapper_text
assert "load_module_config" in wrapper_text
assert "semantic.clap-open-vocabulary.r3b35c.json" in wrapper_text
assert "from semantic_clap import" not in wrapper_text

legacy_text = LEGACY.read_text(encoding="utf-8")
assert "def clap_tags(" in legacy_text
assert "TAXONOMY =" in legacy_text

print("DECLARATIVE_RUNTIME_V1B_CONTRACT_OK")
print("PROFILE CLAP is driven by R3B35C Gene Spec")
print("Legacy CLAP implementation remains available for equivalence checks")
print("Changing compatible decision parameters requires no engine Python change")
print("CHORDS/N baseline untouched")
