from __future__ import annotations

from pathlib import Path

import numpy as np

from pedal import PedalContext, file_sha256
from runtime_deps import prepare_profile_imports

KEY_LABELS = [
    "A major", "Bb major", "B major", "C major", "Db major", "D major",
    "Eb major", "E major", "F major", "F# major", "G major", "Ab major",
    "A minor", "Bb minor", "B minor", "C minor", "C# minor", "D minor",
    "D# minor", "E minor", "F minor", "F# minor", "G minor", "G# minor",
]


def _run(context: PedalContext, model_files: list[Path]) -> dict:
    prepare_profile_imports()
    try:
        import madmom_infer
        from madmom_infer.features.key import CNNKeyRecognitionProcessor
    except Exception as exc:
        raise RuntimeError(
            f"madmom_infer_unavailable:{type(exc).__name__}:{exc}"
        ) from exc

    missing = [str(path) for path in model_files if not path.is_file()]
    if missing:
        raise RuntimeError("madmom_key_models_missing:" + ",".join(missing))

    processor = CNNKeyRecognitionProcessor(
        nn_files=[str(path) for path in model_files],
        backend="numpy",
    )
    prediction = np.asarray(processor(str(context.source)), dtype=np.float64)
    vector = np.ravel(prediction)
    if vector.size != len(KEY_LABELS):
        raise RuntimeError(
            f"madmom_key_unexpected_shape:{tuple(prediction.shape)}"
        )

    order = np.argsort(vector)[::-1]
    candidates = [
        {
            "label": KEY_LABELS[int(index)],
            "score": round(float(vector[int(index)]), 6),
        }
        for index in order
    ]
    best = candidates[0]
    second = candidates[1]
    margin = max(0.0, float(best["score"]) - float(second["score"]))

    return {
        "raw": {
            "probabilities": {
                KEY_LABELS[index]: round(float(vector[index]), 8)
                for index in range(len(KEY_LABELS))
            },
            "candidate_scores": candidates,
        },
        "normalized": {
            "label": best["label"],
            "confidence": round(float(best["score"]), 6),
            "margin": round(margin, 6),
        },
        "calibrated": {
            "status": "model_probability",
            "method": "madmom_cnn_softmax",
            "confidence": round(float(best["score"]), 6),
        },
        "engine": {
            "version": getattr(madmom_infer, "__version__", None),
        },
        "model": {
            "sha256": {
                path.name: file_sha256(path)
                for path in model_files
            },
        },
        "device": "cpu:numpy",
    }


def run_2017(context: PedalContext) -> dict:
    root = (
        context.ai_models_root
        / "audio"
        / "tonal"
        / "madmom-key-cnn"
        / "2017"
    )
    return _run(
        context,
        [root / f"key_cnn_{index}.pkl" for index in range(1, 5)],
    )


def run_2018(context: PedalContext) -> dict:
    root = (
        context.ai_models_root
        / "audio"
        / "tonal"
        / "madmom-key-cnn"
        / "2018"
    )
    return _run(context, [root / "key_cnn.pkl"])
