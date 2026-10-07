from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

import numpy as np
import soundfile as sf


DEFAULT_DB = Path(r"data\benchmark.sqlite")
DEFAULT_STEMS_ROOT = Path(r"H:\temp\EZChords_Benchmark\stems")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_audio_mono(path: Path) -> tuple[np.ndarray, int]:
    y, sr = sf.read(str(path), dtype="float32", always_2d=True)
    if y.shape[1] > 1:
        y = y.mean(axis=1)
    else:
        y = y[:, 0]
    return np.asarray(y, dtype=np.float32), int(sr)


def audio_meta(path: Path) -> dict:
    info = sf.info(str(path))
    return {
        "path": str(path),
        "channels": int(info.channels),
        "sample_rate": int(info.samplerate),
        "frames": int(info.frames),
        "duration_s": float(info.duration),
        "format": str(info.format),
        "subtype": str(info.subtype),
    }


def rms_interval(y: np.ndarray, sr: int, a: float, b: float) -> float:
    ia = max(0, min(len(y), int(round(a * sr))))
    ib = max(ia, min(len(y), int(round(b * sr))))
    if ib <= ia:
        return 0.0
    x = y[ia:ib]
    return float(np.sqrt(np.mean(np.square(x), dtype=np.float64) + 1e-15))


def downsample_abs_envelope(y: np.ndarray, sr: int, hz: int = 100) -> np.ndarray:
    hop = max(1, int(round(sr / hz)))
    n = len(y) // hop
    if n <= 0:
        return np.zeros(0, dtype=np.float32)
    x = np.abs(y[:n * hop]).reshape(n, hop).mean(axis=1)
    x = x - float(np.mean(x))
    s = float(np.std(x))
    if s > 1e-12:
        x = x / s
    return x.astype(np.float32)


def best_lag_seconds(a: np.ndarray, b: np.ndarray, hz: int = 100, max_lag_s: float = 10.0) -> dict:
    n = min(len(a), len(b))
    if n < hz:
        return {"available": False, "reason": "signals too short"}

    a = a[:n]
    b = b[:n]
    max_lag = min(int(round(max_lag_s * hz)), n - 1)

    best = None
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            aa = a[-lag:]
            bb = b[:n + lag]
        elif lag > 0:
            aa = a[:n - lag]
            bb = b[lag:]
        else:
            aa = a
            bb = b

        if len(aa) < hz:
            continue

        score = float(np.dot(aa, bb) / max(1, len(aa)))
        if best is None or score > best[0]:
            best = (score, lag)

    if best is None:
        return {"available": False, "reason": "no valid lag"}

    score, lag = best
    return {
        "available": True,
        "lag_samples_envelope": int(lag),
        "lag_seconds": float(lag / hz),
        "score": float(score),
        "sign_convention": "positive => reconstructed stems are later than master",
    }


def contiguous_true_runs(mask: list[bool], beats: list[float]) -> list[dict]:
    if not mask or not beats:
        return []

    step = float(np.median(np.diff(np.asarray(beats, dtype=float)))) if len(beats) > 1 else 0.5
    out = []
    start = None

    for i, value in enumerate(mask + [False]):
        if value and start is None:
            start = i
        elif not value and start is not None:
            end = i - 1
            a = float(beats[start])
            b = float(beats[end + 1]) if end + 1 < len(beats) else float(beats[end] + step)
            out.append({
                "start_beat": int(start),
                "end_beat": int(end),
                "beats": int(end - start + 1),
                "start_s": a,
                "end_s": b,
                "duration_s": float(b - a),
            })
            start = None

    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", type=int, required=True)
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--stems-root", default=str(DEFAULT_STEMS_ROOT))
    ap.add_argument("--output", default="")
    args = ap.parse_args()

    db = Path(args.db)
    if not db.is_file():
        raise RuntimeError(f"DB not found: {db}")

    con = sqlite3.connect(str(db))
    con.row_factory = sqlite3.Row

    row = con.execute(
        "SELECT * FROM benchmark_runs WHERE id=?",
        (args.run_id,),
    ).fetchone()

    if row is None:
        raise RuntimeError(f"run {args.run_id} not found")

    result = json.loads(row["result_json"] or "{}")
    if not result:
        raise RuntimeError(f"run {args.run_id} has no result_json")

    audio = Path(row["input_path"])
    if not audio.is_file():
        raise RuntimeError(f"audio not found: {audio}")

    audio_hash = sha256_file(audio)
    storage = Path(args.stems_root) / audio_hash
    current = storage / "current.json"
    if not current.is_file():
        raise RuntimeError(f"cached stems current.json not found: {current}")

    current_payload = json.loads(current.read_text(encoding="utf-8"))
    run_name = str(current_payload.get("run", ""))
    stem_run = storage / "runs" / run_name

    manifest_path = stem_run / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else None

    beats = [float(x) for x in result.get("beat_grid_s", [])]
    nchord = result.get("no_chord_benchmark", {})
    variants = nchord.get("variants", [])
    active_name = nchord.get("active_variant")

    active = next((v for v in variants if v.get("name") == active_name), None)
    if active is None:
        active = next((v for v in variants if v.get("name") == "E_positive_harmonic_support"), None)
    if active is None:
        raise RuntimeError("positive harmonic support diagnostic not found in result_json")

    support_rows = active.get("beat_support", [])
    active_mask = [bool(x) for x in active.get("mask", [])]
    n_runs = contiguous_true_runs(active_mask, beats)

    stem_names = ("bass", "guitar", "piano", "other")
    all_stem_names = ("lead_vocals", "backing_vocals", "drums", "bass", "guitar", "piano", "other")

    stem_audio = {}
    stem_meta = {}

    for name in all_stem_names:
        p = stem_run / f"{name}.wav"
        if p.is_file():
            stem_meta[name] = audio_meta(p)
            stem_audio[name] = read_audio_mono(p)

    beat_rows = []
    if beats:
        step = float(np.median(np.diff(np.asarray(beats)))) if len(beats) > 1 else 0.5
        support_by_beat = {
            int(x["beat"]): x
            for x in support_rows
            if isinstance(x, dict) and "beat" in x
        }

        for i, a in enumerate(beats):
            b = beats[i + 1] if i + 1 < len(beats) else a + step
            row_out = {
                "beat": int(i),
                "start_s": float(a),
                "end_s": float(b),
                "duration_s": float(b - a),
                "rms": {},
            }

            for name in stem_names:
                if name in stem_audio:
                    y, sr = stem_audio[name]
                    row_out["rms"][name] = rms_interval(y, sr, a, b)

            if i in support_by_beat:
                row_out["classifier"] = support_by_beat[i]

            beat_rows.append(row_out)

    alignment = {"available": False, "reason": "analysis input.wav not found"}
    analysis_audio = None

    candidates = sorted(Path("results").glob(f"run-{args.run_id:06d}-*/input.wav"))
    if candidates:
        analysis_audio = candidates[-1]

    if analysis_audio and analysis_audio.is_file() and stem_audio:
        master, master_sr = read_audio_mono(analysis_audio)

        usable = [
            (name, y, sr)
            for name, (y, sr) in stem_audio.items()
            if sr == master_sr
        ]

        if usable:
            min_len = min([len(master)] + [len(y) for _, y, _ in usable])
            recon = np.zeros(min_len, dtype=np.float32)

            for _, y, _ in usable:
                recon += y[:min_len]

            recon /= max(1, len(usable))

            master_env = downsample_abs_envelope(master[:min_len], master_sr, hz=100)
            recon_env = downsample_abs_envelope(recon, master_sr, hz=100)

            alignment = best_lag_seconds(master_env, recon_env, hz=100, max_lag_s=10.0)
            alignment["master_path"] = str(analysis_audio)
            alignment["reconstruction_stems"] = [name for name, _, _ in usable]

    report = {
        "run": {
            "id": int(args.run_id),
            "status": row["status"],
            "progress": row["progress"],
            "input_path": str(audio),
            "audio_sha256": audio_hash,
        },
        "engine_version": result.get("engine_version"),
        "tempo": result.get("tempo"),
        "signature": result.get("signature"),
        "meter": result.get("meter"),
        "convergence": result.get("convergence"),
        "beat_count": len(beats),
        "beat_grid_s": beats,
        "active_variant": active_name,
        "n_runs": n_runs,
        "stem_storage": {
            "root": str(storage),
            "current": current_payload,
            "run_dir": str(stem_run),
            "manifest": manifest,
            "wav_meta": stem_meta,
        },
        "global_alignment_test": alignment,
        "beat_diagnostics": beat_rows,
    }

    out = Path(args.output) if args.output else Path("diagnostics") / f"run-{args.run_id}-timing.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"RUN={args.run_id}")
    print(f"ENGINE={report['engine_version']}")
    print(f"SIGNATURE={report['signature']} TEMPO={report['tempo']}")
    print(f"ACTIVE_VARIANT={active_name}")
    print(f"N_RUNS={len(n_runs)}")

    for idx, r in enumerate(n_runs[:30], start=1):
        print(
            f"N{idx:02d}: beats {r['start_beat']}..{r['end_beat']} "
            f"t={r['start_s']:.3f}..{r['end_s']:.3f}s "
            f"len={r['beats']} beats"
        )

    if alignment.get("available"):
        print(
            "STEM_GLOBAL_LAG="
            f"{alignment['lag_seconds']:+.3f}s "
            "(positive means stems later than master)"
        )
    else:
        print("STEM_GLOBAL_LAG=UNAVAILABLE")
        if alignment.get("reason"):
            print(f"  reason={alignment['reason']}")

    print(f"REPORT={out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
