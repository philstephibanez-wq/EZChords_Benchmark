from __future__ import annotations

import numpy as np

from pedal import PedalContext


MAJOR = np.array(
    [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88],
    dtype=float,
)
MINOR = np.array(
    [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17],
    dtype=float,
)
NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def estimate_key(chroma: np.ndarray) -> dict:
    x = np.nan_to_num(np.asarray(chroma, dtype=float))
    if x.sum() <= 0:
        return {
            "label": None,
            "tonic": None,
            "mode": None,
            "confidence": 0.0,
        }

    x = (x - x.mean()) / (x.std() + 1e-9)
    scores = []
    for index in range(12):
        for mode, profile in (("major", MAJOR), ("minor", MINOR)):
            p = np.roll(profile, index)
            p = (p - p.mean()) / (p.std() + 1e-9)
            scores.append((float(np.mean(x * p)), index, mode))
    scores.sort(reverse=True)

    best, second = scores[0], scores[1]
    margin = max(0.0, best[0] - second[0])
    confidence = max(0.0, min(1.0, margin / 0.25))
    tonic = NAMES[best[1]]

    return {
        "label": f"{tonic} {best[2]}",
        "tonic": tonic,
        "mode": best[2],
        "confidence": round(confidence, 4),
        "score": round(best[0], 6),
        "margin": round(margin, 6),
        "candidate_scores": [
            {
                "label": f"{NAMES[index]} {mode}",
                "score": round(score, 6),
            }
            for score, index, mode in scores
        ],
    }


def run(context: PedalContext) -> dict:
    import librosa

    chroma = librosa.feature.chroma_cqt(y=context.y, sr=context.sr)
    result = estimate_key(np.nanmean(chroma, axis=1))
    return {
        "raw": {
            "mean_chroma": np.nanmean(chroma, axis=1).round(8).tolist(),
            "candidate_scores": result.get("candidate_scores", []),
        },
        "normalized": {
            key: value
            for key, value in result.items()
            if key != "candidate_scores"
        },
        "calibrated": {
            "status": "heuristic",
            "method": "ks_best_vs_second_margin",
            "confidence": result.get("confidence"),
        },
        "engine": {"version": getattr(librosa, "__version__", None)},
    }
