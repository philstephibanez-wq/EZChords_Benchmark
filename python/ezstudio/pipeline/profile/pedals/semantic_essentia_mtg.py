from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from pedal import PedalContext, file_sha256


def _labels(meta_path: Path) -> list[str]:
    try:
        obj = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    stack = [obj]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for key, value in cur.items():
                if key in ("classes", "labels") and isinstance(value, list) and value:
                    return [str(item) for item in value]
                if isinstance(value, (dict, list)):
                    stack.append(value)
        elif isinstance(cur, list):
            stack.extend(cur)
    return []


def _aggregate(
    predictions: np.ndarray,
    labels: list[str],
    top_n: int,
) -> list[dict]:
    p = np.asarray(predictions, dtype=float)
    mean = np.nanmean(p, axis=0) if p.ndim > 1 else p
    mean = np.ravel(mean)
    if len(labels) != len(mean):
        labels = [f"class_{index}" for index in range(len(mean))]
    order = np.argsort(mean)[::-1][:top_n]
    return [
        {
            "label": labels[int(index)],
            "score": round(float(mean[int(index)]), 4),
            "score_type": "model_output_mean",
        }
        for index in order
        if float(mean[int(index)]) > 0
    ]


def run(context: PedalContext) -> dict:
    try:
        import essentia
        from essentia.standard import (
            MonoLoader,
            TensorflowPredict2D,
            TensorflowPredictEffnetDiscogs,
        )
    except Exception as exc:
        raise RuntimeError(
            f"essentia_unavailable:{type(exc).__name__}:{exc}"
        ) from exc

    root = context.model_root
    files = {
        "embedding": root / "discogs-effnet-bs64-1.pb",
        "genre": root / "mtg_jamendo_genre-discogs-effnet-1.pb",
        "genre_meta": root / "mtg_jamendo_genre-discogs-effnet-1.json",
        "instrument": root / "mtg_jamendo_instrument-discogs-effnet-1.pb",
        "instrument_meta": root / "mtg_jamendo_instrument-discogs-effnet-1.json",
        "mood": root / "mtg_jamendo_moodtheme-discogs-effnet-1.pb",
        "mood_meta": root / "mtg_jamendo_moodtheme-discogs-effnet-1.json",
        "gender": root / "gender-discogs-effnet-1.pb",
        "gender_meta": root / "gender-discogs-effnet-1.json",
        "voice": root / "voice_instrumental-discogs-effnet-1.pb",
        "voice_meta": root / "voice_instrumental-discogs-effnet-1.json",
    }
    missing = [name for name, path in files.items() if not path.is_file()]
    if missing:
        raise RuntimeError("profile_models_missing:" + ",".join(missing))

    audio = MonoLoader(
        filename=str(context.source),
        sampleRate=16000,
        resampleQuality=4,
    )()
    embeddings = TensorflowPredictEffnetDiscogs(
        graphFilename=str(files["embedding"]),
        output="PartitionedCall:1",
    )(audio)

    normalized = {
        "genre": [],
        "instrumentation": [],
        "mood": [],
        "voice": [],
    }
    for key, meta_key, out_key, top_n in (
        ("genre", "genre_meta", "genre", 8),
        ("instrument", "instrument_meta", "instrumentation", 12),
        ("mood", "mood_meta", "mood", 8),
        ("gender", "gender_meta", "voice", 4),
        ("voice", "voice_meta", "voice", 4),
    ):
        pred = TensorflowPredict2D(graphFilename=str(files[key]))(embeddings)
        values = _aggregate(
            np.asarray(pred),
            _labels(files[meta_key]),
            top_n,
        )
        if out_key == "voice":
            normalized[out_key].extend(values)
        else:
            normalized[out_key] = values

    return {
        "raw": {
            "embedding_shape": list(np.asarray(embeddings).shape),
            "model_sha256": {
                name: file_sha256(path)
                for name, path in files.items()
                if path.suffix == ".pb"
            },
        },
        "normalized": normalized,
        "engine": {"version": getattr(essentia, "__version__", None)},
        "model": {
            "id": "essentia-discogs-effnet+mtg-jamendo",
            "path": str(root),
        },
        "device": "tensorflow-runtime",
    }
