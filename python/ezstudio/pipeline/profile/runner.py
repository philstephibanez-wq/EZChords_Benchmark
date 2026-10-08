from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np

from meter_shared import estimate_meter_from_chords_engine
from semantic_clap import clap_tags

R3B10_PROFILE_ENRICHMENT = True

SCHEMA = "ezstudio.profile.v1"


def write_progress(path: Path, percent: int, message: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"percent": int(percent), "progress": int(percent), "message": message, "updated_at": time.time()}, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def estimate_key(chroma: np.ndarray) -> dict:
    major = np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88], dtype=float)
    minor = np.array([6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.75,3.98,2.69,3.34,3.17], dtype=float)
    names = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
    x = np.nan_to_num(np.asarray(chroma, dtype=float))
    if x.sum() <= 0:
        return {"label": None, "tonic": None, "mode": None, "confidence": 0.0}
    x = (x - x.mean()) / (x.std() + 1e-9)
    scores = []
    for i in range(12):
        for mode, profile in (("major", major), ("minor", minor)):
            p = np.roll(profile, i)
            p = (p - p.mean()) / (p.std() + 1e-9)
            scores.append((float(np.mean(x * p)), i, mode))
    scores.sort(reverse=True)
    best, second = scores[0], scores[1]
    margin = max(0.0, best[0] - second[0])
    confidence = max(0.0, min(1.0, margin / 0.25))
    tonic = names[best[1]]
    return {"label": f"{tonic} {best[2]}", "tonic": tonic, "mode": best[2], "confidence": round(confidence, 4), "score": round(best[0], 6)}


def estimate_meter(onset_env: np.ndarray, beat_frames: np.ndarray) -> dict:
    candidates = [2, 3, 4, 6, 9, 12]
    if len(beat_frames) < 12:
        return {"label": None, "numerator": None, "denominator": None, "confidence": 0.0}
    beat_energy = onset_env[np.clip(beat_frames.astype(int), 0, len(onset_env)-1)]
    scores = []
    for n in candidates:
        buckets = np.zeros(n, dtype=float)
        counts = np.zeros(n, dtype=float)
        for i, value in enumerate(beat_energy):
            buckets[i % n] += float(value)
            counts[i % n] += 1.0
        means = buckets / np.maximum(counts, 1.0)
        accent = float((means.max() - np.median(means)) / (np.std(means) + 1e-9))
        periodic = float(np.std(means) / (np.mean(np.abs(means)) + 1e-9))
        prior = {4:0.12,3:0.08,6:0.06,2:0.03,9:0.0,12:0.0}[n]
        scores.append((accent + 0.35*periodic + prior, n))
    scores.sort(reverse=True)
    best, second = scores[0], scores[1]
    confidence = max(0.05, min(0.85, max(0.0, best[0]-second[0]) / 1.5))
    n = best[1]
    d = 8 if n in (6,9,12) else 4
    return {
        "label": f"{n}/{d}",
        "numerator": n,
        "denominator": d,
        "confidence": round(confidence, 4),
        "candidate_scores": {f"{c}/{8 if c in (6,9,12) else 4}": round(s, 6) for s, c in scores},
    }


def _labels(meta_path: Path) -> list[str]:
    try:
        obj = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    stack = [obj]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for k, v in cur.items():
                if k in ("classes", "labels") and isinstance(v, list) and v:
                    return [str(x) for x in v]
                if isinstance(v, (dict, list)):
                    stack.append(v)
        elif isinstance(cur, list):
            stack.extend(cur)
    return []


def _aggregate(predictions: np.ndarray, labels: list[str], top_n: int) -> list[dict]:
    p = np.asarray(predictions, dtype=float)
    mean = np.nanmean(p, axis=0) if p.ndim > 1 else p
    mean = np.ravel(mean)
    if len(labels) != len(mean):
        labels = [f"class_{i}" for i in range(len(mean))]
    order = np.argsort(mean)[::-1][:top_n]
    return [{"label": labels[int(i)], "score": round(float(mean[int(i)]), 4)} for i in order if float(mean[int(i)]) > 0]


def essentia_tags(source: Path, model_root: Path) -> tuple[dict, list[str]]:
    result = {"available": False, "backend": "essentia-discogs-effnet", "genre": [], "instrumentation": [], "mood": [], "voice": []}
    warnings: list[str] = []
    try:
        from essentia.standard import MonoLoader, TensorflowPredictEffnetDiscogs, TensorflowPredict2D
    except Exception as exc:
        warnings.append(f"essentia_unavailable:{type(exc).__name__}")
        return result, warnings

    files = {
        "embedding": model_root / "discogs-effnet-bs64-1.pb",
        "genre": model_root / "mtg_jamendo_genre-discogs-effnet-1.pb",
        "genre_meta": model_root / "mtg_jamendo_genre-discogs-effnet-1.json",
        "instrument": model_root / "mtg_jamendo_instrument-discogs-effnet-1.pb",
        "instrument_meta": model_root / "mtg_jamendo_instrument-discogs-effnet-1.json",
        "mood": model_root / "mtg_jamendo_moodtheme-discogs-effnet-1.pb",
        "mood_meta": model_root / "mtg_jamendo_moodtheme-discogs-effnet-1.json",
        "gender": model_root / "gender-discogs-effnet-1.pb",
        "gender_meta": model_root / "gender-discogs-effnet-1.json",
        "voice": model_root / "voice_instrumental-discogs-effnet-1.pb",
        "voice_meta": model_root / "voice_instrumental-discogs-effnet-1.json",
    }
    missing = [k for k,p in files.items() if not p.is_file()]
    if missing:
        warnings.append("profile_models_missing:" + ",".join(missing))
        return result, warnings

    audio = MonoLoader(filename=str(source), sampleRate=16000, resampleQuality=4)()
    emb = TensorflowPredictEffnetDiscogs(graphFilename=str(files["embedding"]), output="PartitionedCall:1")(audio)
    for key, meta_key, out_key, top_n in (
        ("genre","genre_meta","genre",8),
        ("instrument","instrument_meta","instrumentation",12),
        ("mood","mood_meta","mood",8),
        ("gender","gender_meta","voice",4),
        ("voice","voice_meta","voice",4),
    ):
        pred = TensorflowPredict2D(graphFilename=str(files[key]))(emb)
        vals = _aggregate(np.asarray(pred), _labels(files[meta_key]), top_n)
        if out_key == "voice":
            result[out_key].extend(vals)
        else:
            result[out_key] = vals
    result["available"] = True
    return result, warnings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--audio-hash", required=True)
    ap.add_argument("--output-path", required=True)
    ap.add_argument("--progress-file", required=True)
    args = ap.parse_args()

    source = Path(args.source).resolve()
    output = Path(args.output_path).resolve()
    progress = Path(args.progress_file).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    write_progress(progress, 3, "PROFILE: chargement")
    import librosa
    y, sr = librosa.load(str(source), sr=22050, mono=True)
    if y.size == 0:
        raise RuntimeError("profile_audio_empty")

    duration = float(librosa.get_duration(y=y, sr=sr))
    write_progress(progress, 20, "PROFILE: tempo / rythme")
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo_value, beat_frames = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr, units="frames")
    tempo = float(np.asarray(tempo_value).reshape(-1)[0]) if np.size(tempo_value) else 0.0
    meter_warnings = []
    try:
        meter = estimate_meter_from_chords_engine(
            np.asarray(y, dtype=np.float32),
            int(sr),
            confidence_threshold=0.50,
        )
    except Exception as exc:
        meter = {
            "available": False,
            "label": None,
            "suggested_label": None,
            "numerator": None,
            "denominator": None,
            "confidence": 0.0,
            "candidate_scores": {},
            "source": "chords_metric_r9",
            "reason": f"{type(exc).__name__}:{exc}",
        }
        meter_warnings.append(
            f"profile_meter_unavailable:{type(exc).__name__}:{exc}"
        )

    write_progress(progress, 42, "PROFILE: tonalité")
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    key = estimate_key(np.nanmean(chroma, axis=1))

    write_progress(progress, 58, "PROFILE: descripteurs")
    rms = librosa.feature.rms(y=y)[0]
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.85)[0]
    zcr = librosa.feature.zero_crossing_rate(y)[0]

    characteristics = {
        "duration_seconds": round(duration, 3),
        "tempo": {"bpm": round(tempo, 3), "confidence": None, "source": "librosa.beat"},
        "time_signature": meter,
        "key": key,
        "dynamics": {"rms_mean": round(float(np.mean(rms)), 8), "rms_peak": round(float(np.max(rms)), 8)},
        "spectral": {
            "centroid_hz_mean": round(float(np.mean(centroid)), 3),
            "rolloff_85_hz_mean": round(float(np.mean(rolloff)), 3),
            "zero_crossing_rate_mean": round(float(np.mean(zcr)), 8),
        },
    }

    write_progress(progress, 72, "PROFILE: style / instruments")
    model_root = Path(os.getenv("EZSTUDIO_PROFILE_MODELS", r"H:\EZStudioModels\profile"))
    tagging, warnings = essentia_tags(source, model_root)
    if not bool(tagging.get("available")):
        clap_result, clap_warnings = clap_tags(source, model_root)
        warnings.extend(clap_warnings)
        if bool(clap_result.get("available")):
            tagging = clap_result

    warnings.extend(meter_warnings)

    result = {
        "schema": SCHEMA,
        "audio_sha256": args.audio_hash,
        "source_sha256": sha256(source),
        "characteristics": characteristics,
        "tagging": tagging,
        "warnings": warnings,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "librosa": getattr(librosa, "__version__", ""),
            "profile_models": str(model_root),
            "profile_semantic_backend": str(tagging.get("backend") or ""),
            "profile_meter_source": str(meter.get("source") or ""),
        },
        "automatic_next_stage": False,
    }

    write_progress(progress, 94, "PROFILE: écriture ADN")
    tmp = output.with_suffix(".tmp")
    tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(output)
    write_progress(progress, 100, "PROFILE terminé")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
