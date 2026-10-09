from __future__ import annotations

from gene import GeneContext
from semantic_clap import MODEL_NAME, clap_tags


def run(context: GeneContext) -> dict:
    result, warnings = clap_tags(context.source, context.model_root)
    if not bool(result.get("available")):
        raise RuntimeError(
            ";".join(warnings) if warnings else "clap_unavailable"
        )

    normalized = {
        "genre": list(result.get("genre") or []),
        "instrumentation": list(result.get("instrumentation") or []),
        "mood": list(result.get("mood") or []),
        "voice": list(result.get("voice") or []),
    }
    return {
        "raw": {
            "chunks": result.get("chunks"),
            "chunk_seconds": result.get("chunk_seconds"),
            "score_semantics": result.get("score_semantics"),
            "temporal": result.get("temporal") or {},
        },
        "normalized": normalized,
        "warnings": warnings,
        "model": {
            "id": MODEL_NAME,
            "path": str(context.model_root / "clap-htsat-unfused"),
        },
        "device": "cuda:0",
        "engine": {
            "version": result.get("transformers_version"),
        },
    }
