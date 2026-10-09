from __future__ import annotations

import numpy as np

from meter_shared import estimate_meter_from_chords_engine
from gene import GeneContext


def run(context: GeneContext) -> dict:
    result = estimate_meter_from_chords_engine(
        np.asarray(context.y, dtype=np.float32),
        int(context.sr),
        confidence_threshold=0.50,
    )
    confidence = float(result.get("confidence") or 0.0)
    return {
        "raw": result,
        "normalized": result,
        "calibrated": {
            "status": "source_specific_threshold",
            "method": "chords_metric_r9_confidence_threshold_0.50",
            "confidence": round(confidence, 4),
        },
        "model": {
            "id": "beat-this-final0",
            "path": result.get("beat_this_checkpoint"),
        },
        "device": "cuda:0",
    }
