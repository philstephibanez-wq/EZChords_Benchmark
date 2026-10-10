from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "python" / "ezstudio" / "pipeline" / "profile" / "canonical_profile.py"
REGISTRY = ROOT / "python" / "ezstudio" / "pipeline" / "profile" / "gene_registry.py"
RUNNER = ROOT / "python" / "ezstudio" / "pipeline" / "profile" / "runner.py"

spec = importlib.util.spec_from_file_location("canonical_profile", MODULE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

semantic = {
    "genre": {
        "per_engine": {
            "semantic.clap-open-vocabulary": [
                {"label": "soft rock", "score": 0.41, "score_type": "category_relative_softmax"},
                {"label": "pop", "score": 0.22, "score_type": "category_relative_softmax"},
            ]
        }
    },
    "voice": {
        "per_engine": {
            "semantic.clap-open-vocabulary": [
                {"label": "backing vocals", "score": 0.28},
                {"label": "choir", "score": 0.03},
                {"label": "vocal harmonies", "score": 0.01},
            ]
        }
    },
    "audioset": {
        "accepted": [
            {
                "label": "Singing",
                "support": 2,
                "decision": "accepted",
                "source_evidence": [
                    {"gene": "semantic.panns-cnn14"},
                    {"gene": "semantic.passt-audioset"},
                ],
            }
        ],
        "agreements": [
            {
                "label": "Singing",
                "support": 2,
                "decision": "accepted",
                "source_evidence": [
                    {"gene": "semantic.panns-cnn14"},
                    {"gene": "semantic.passt-audioset"},
                ],
            },
            {
                "label": "Chant",
                "support": 1,
                "decision": "uncertain",
                "source_evidence": [{"gene": "semantic.panns-cnn14"}],
            },
            {
                "label": "Vocal music",
                "support": 1,
                "decision": "uncertain",
                "source_evidence": [{"gene": "semantic.passt-audioset"}],
            },
        ],
    },
}

genre = module.build_genre_hierarchy(semantic)
assert genre["primary"]["genre_family"] == "rock"
assert genre["primary"]["genre"] == "rock"
assert genre["primary"]["subgenre"] == "soft rock"
assert "style" not in repr(genre).casefold()

vocals = module.build_vocal_profile(semantic)
assert vocals["dimensions"]["lead_vocal"]["decision"] == "present"
assert vocals["dimensions"]["backing_vocals"]["decision"] == "possible"
assert vocals["dimensions"]["choir"]["decision"] == "inconclusive"
assert vocals["usable_for_stems"] is False

registry_text = REGISTRY.read_text(encoding="utf-8")
runner_text = RUNNER.read_text(encoding="utf-8")
assert "profile-r3b35c-canonical-genre-vocals" in registry_text
assert '"genre_hierarchy": build_genre_hierarchy(semantic)' in registry_text
assert '"vocal_profile": build_vocal_profile(semantic)' in registry_text
assert '"genre_hierarchy": consensus.get("genre_hierarchy") or {}' in runner_text
assert '"vocal_profile": consensus.get("vocal_profile") or {}' in runner_text
assert "R3B35C_CANONICAL_PROFILE = True" in runner_text

print("PROFILE_R3B35C_CONTRACT_OK")
