from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np


def estimate_meter_from_chords_engine(
    y: np.ndarray,
    sr: int,
    *,
    confidence_threshold: float = 0.50,
) -> dict:
    """
    Reuse the metric logic already validated in python/engine.py without
    launching a CHORDS run.
    """
    project_python = Path(__file__).resolve().parents[3]
    if str(project_python) not in sys.path:
        sys.path.insert(0, str(project_python))

    dep_root = Path(
        os.getenv("EZSTUDIO_DEP_ROOT", r"H:\temp\EZStudio_lab\deps")
    )
    if dep_root.is_dir() and str(dep_root) not in sys.path:
        sys.path.append(str(dep_root))

    import librosa
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("profile_meter_cuda_required")

    from engine import (
        z,
        sample_frames,
        sample_times,
        sigmoid,
        bass_feature,
        harmonic_novelty,
        auto_signature,
        refine_duple_signature_with_beat_this,
    )

    try:
        from beat_this.inference import Audio2Frames
    except Exception as exc:
        raise RuntimeError(
            f"profile_meter_beat_this_unavailable:{type(exc).__name__}:{exc}"
        ) from exc

    hop = 512
    _, perc = librosa.effects.hpss(y)

    tempo_arr, beats = librosa.beat.beat_track(
        y=perc,
        sr=sr,
        hop_length=hop,
        units="time",
        trim=False,
    )
    beats = np.asarray(beats, dtype=float)

    if len(beats) < 12:
        return {
            "available": True,
            "label": None,
            "suggested_label": None,
            "numerator": None,
            "denominator": None,
            "confidence": 0.0,
            "candidate_scores": {},
            "source": "chords_metric_r9",
            "reason": "too_few_beats",
        }

    bf = librosa.time_to_frames(beats, sr=sr, hop_length=hop)
    onset = sample_frames(
        librosa.onset.onset_strength(y=perc, sr=sr, hop_length=hop),
        bf,
    )
    bass = bass_feature(y, sr, hop, bf)
    harm = harmonic_novelty(y, sr, hop, bf)

    meter = auto_signature(z(onset), z(bass), z(harm))
    initial_signature = str(meter["signature"])

    checkpoint = Path(
        os.getenv(
            "EZSTUDIO_BEAT_THIS_CHECKPOINT",
            r"H:\EZStudioModels\beat_this\beat_this-final0.ckpt",
        )
    )
    if not checkpoint.is_file():
        raise RuntimeError(
            f"profile_meter_checkpoint_missing:{checkpoint}"
        )

    model = Audio2Frames(
        checkpoint_path=str(checkpoint),
        device="cuda",
        float16=False,
    )
    _, db = model(y, sr)
    bt = sample_times(
        sigmoid(db.detach().float().cpu().numpy()),
        beats,
    )

    signature, refinement = refine_duple_signature_with_beat_this(
        initial_signature,
        bt,
    )

    confidence = float(meter.get("confidence") or 0.0)
    confident = confidence >= float(confidence_threshold)
    numerator = int(signature.split("/", 1)[0])
    denominator = int(signature.split("/", 1)[1])

    return {
        "available": True,
        "label": signature if confident else None,
        "suggested_label": signature,
        "numerator": numerator if confident else None,
        "denominator": denominator if confident else None,
        "confidence": round(confidence, 4),
        "confidence_threshold": float(confidence_threshold),
        "candidate_scores": {
            str(k): round(float(v), 6)
            for k, v in (meter.get("scores") or {}).items()
        },
        "initial_signature": initial_signature,
        "duple_refinement": refinement,
        "source": "chords_metric_r9",
        "beat_this_checkpoint": str(checkpoint),
        "tempo_bpm": float(np.asarray(tempo_arr).squeeze()),
    }
