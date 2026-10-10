from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "python" / "ezstudio" / "runtime"
SPEC = ROOT / "adn" / "specs" / "profile" / "semantic.clap-open-vocabulary.r3b35c.json"

sys.path.insert(0, str(ROOT / "python"))

from ezstudio.runtime.gene_spec import load_gene_spec  # noqa: E402
from ezstudio.runtime.decision import apply_decision  # noqa: E402
from ezstudio.runtime.engine_registry import EngineAdapterRegistry, EngineAdapterError  # noqa: E402


def main() -> int:
    doc = load_gene_spec(SPEC)
    assert doc.gene_id == "semantic.clap-open-vocabulary"
    assert doc.region == "profile"
    assert doc.revision == "r3b35c-compat-v1"
    assert len(doc.sha256) == 64

    families = doc.data["taxonomy"]["families"]
    assert families["genre"][0] == "chanson française"
    assert "singer-songwriter" in families["genre"]
    assert len(families["instrumentation"]) == 25
    assert len(families["voice"]) == 11

    decision = doc.data["decision"]["families"]
    assert decision["genre"] == {"mode": "compatibility_top_k", "top_k": 6}
    assert decision["instrumentation"] == {"mode": "compatibility_top_k", "top_k": 12}

    rows = [
        {"label": "a", "score": 0.8},
        {"label": "b", "score": 0.6},
        {"label": "c", "score": 0.2},
    ]
    compat = apply_decision(rows, {"mode": "compatibility_top_k", "top_k": 2})
    assert [x["label"] for x in compat["selected"]] == ["a", "b"]
    abstain = apply_decision(rows, {
        "mode": "multilabel_with_abstention",
        "threshold": 0.9,
        "max_labels": 2,
    })
    assert abstain["abstained"] is True

    registry = EngineAdapterRegistry()
    registry.register("dummy", lambda spec, context: {"ok": True, "spec": spec["gene"]["id"]})
    assert registry.execute("dummy", doc.data, None)["ok"] is True
    try:
        registry.execute("missing", doc.data, None)
    except EngineAdapterError:
        pass
    else:
        raise AssertionError("missing adapter must fail explicitly")

    print("DECLARATIVE_RUNTIME_V1A_CONTRACT_OK")
    print("Common runtime: profile/stems/chords/lyrics")
    print("PROFILE R3B35C CLAP Gene Spec encoded without changing execution")
    print("No scientific mutation in V1A")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
