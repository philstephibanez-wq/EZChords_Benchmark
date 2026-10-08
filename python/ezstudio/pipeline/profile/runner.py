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

from pedal import PedalContext, PedalSpec
from pedalboard import Pedalboard
from pedals import descriptors_librosa
from pedals import meter_chords_shared
from pedals import rhythm_librosa
from pedals import semantic_clap_open_vocab
from pedals import semantic_essentia_mtg
from pedals import tonal_ks

R3B11_PROFILE_PEDALBOARD = True
SCHEMA = "ezstudio.profile.v1"


def write_progress(path: Path, percent: int, message: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(
            {
                "percent": int(percent),
                "progress": int(percent),
                "message": message,
                "updated_at": time.time(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    tmp.replace(path)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _pedal_by_id(
    pedalboard_result: dict,
    pedal_id: str,
) -> dict | None:
    for record in pedalboard_result.get("pedals") or []:
        if record.get("id") == pedal_id:
            return record
    return None


def _normalized(record: dict | None) -> dict:
    if not isinstance(record, dict):
        return {}
    value = record.get("normalized")
    return value if isinstance(value, dict) else {}


def _legacy_projection(
    pedalboard_result: dict,
    duration: float,
) -> tuple[dict, dict, list[str]]:
    rhythm = _pedal_by_id(pedalboard_result, "rhythm.librosa-beat")
    meter = _pedal_by_id(pedalboard_result, "meter.chords-shared-r9")
    tonal = _pedal_by_id(pedalboard_result, "tonal.krumhansl-schmuckler")
    descriptors = _pedal_by_id(pedalboard_result, "descriptors.librosa-lowlevel")
    essentia = _pedal_by_id(pedalboard_result, "semantic.essentia-discogs-mtg")
    clap = _pedal_by_id(pedalboard_result, "semantic.clap-open-vocabulary")

    rhythm_n = _normalized(rhythm)
    meter_n = _normalized(meter)
    tonal_n = _normalized(tonal)
    descriptors_n = _normalized(descriptors)

    characteristics = {
        "duration_seconds": round(duration, 3),
        "tempo": {
            "bpm": rhythm_n.get("bpm", 0.0),
            "confidence": rhythm_n.get("confidence"),
            "source": rhythm_n.get("source", "librosa.beat"),
        },
        "time_signature": meter_n,
        "key": tonal_n,
        "dynamics": descriptors_n.get("dynamics") or {},
        "spectral": descriptors_n.get("spectral") or {},
    }

    # Legacy compatibility only:
    # preserve the historical primary semantic projection while R3B11 records
    # every semantic pedal independently in pedalboard.pedals.
    if essentia and essentia.get("status") == "ok":
        tagging = _normalized(essentia)
        tagging["available"] = True
        tagging["backend"] = "essentia-discogs-effnet"
    elif clap and clap.get("status") == "ok":
        tagging = _normalized(clap)
        tagging["available"] = True
        tagging["backend"] = "clap-zero-shot"
    else:
        tagging = {
            "available": False,
            "backend": None,
            "genre": [],
            "instrumentation": [],
            "mood": [],
            "voice": [],
        }

    warnings: list[str] = []
    for record in pedalboard_result.get("pedals") or []:
        warnings.extend(str(item) for item in (record.get("warnings") or []))
        if record.get("status") == "error":
            error = record.get("error") or {}
            warnings.append(
                "profile_pedal_error:"
                + str(record.get("id"))
                + ":"
                + str(error.get("type") or "")
                + ":"
                + str(error.get("message") or "")
            )

    return characteristics, tagging, warnings


def _model_roots() -> tuple[Path, Path]:
    ai_root = Path(os.getenv("AI_MODELS_ROOT", r"H:\AIModels"))
    profile_root = Path(
        os.getenv(
            "EZSTUDIO_PROFILE_MODELS",
            str(ai_root / "audio" / "profile"),
        )
    )
    return ai_root, profile_root


def build_pedalboard(profile_root: Path) -> Pedalboard:
    return (
        Pedalboard()
        .add(
            PedalSpec(
                pedal_id="rhythm.librosa-beat",
                display_name="Librosa Beat Tracker",
                family="rhythm",
                order=10,
                engine="librosa",
                parameters={"mono": True, "analysis_sample_rate": 22050},
            ),
            rhythm_librosa.run,
        )
        .add(
            PedalSpec(
                pedal_id="meter.chords-shared-r9",
                display_name="CHORDS Shared Meter R9",
                family="meter",
                order=20,
                engine="chords_metric_r9",
                model_id="beat-this-final0",
                model_path=str(
                    Path(
                        os.getenv(
                            "EZSTUDIO_BEAT_THIS_CHECKPOINT",
                            r"H:\AIModels\audio\rhythm\beat-this\beat_this-final0.ckpt",
                        )
                    )
                ),
                device="cuda:0",
                thresholds={"confidence": 0.50},
            ),
            meter_chords_shared.run,
        )
        .add(
            PedalSpec(
                pedal_id="tonal.krumhansl-schmuckler",
                display_name="Krumhansl-Schmuckler Key",
                family="tonal",
                order=30,
                engine="librosa-chroma-cqt+ks",
                parameters={"chroma": "CQT"},
            ),
            tonal_ks.run,
        )
        .add(
            PedalSpec(
                pedal_id="descriptors.librosa-lowlevel",
                display_name="Librosa Low-Level Descriptors",
                family="descriptors",
                order=40,
                engine="librosa",
                parameters={"rolloff_percent": 0.85},
            ),
            descriptors_librosa.run,
        )
        .add(
            PedalSpec(
                pedal_id="semantic.essentia-discogs-mtg",
                display_name="Essentia Discogs + MTG",
                family="semantic",
                order=50,
                engine="essentia",
                model_id="discogs-effnet+mtg-jamendo",
                model_path=str(profile_root),
            ),
            semantic_essentia_mtg.run,
        )
        .add(
            PedalSpec(
                pedal_id="semantic.clap-open-vocabulary",
                display_name="CLAP Open Vocabulary",
                family="semantic",
                order=60,
                engine="transformers.CLAP",
                model_id="laion/clap-htsat-unfused",
                model_path=str(profile_root / "clap-htsat-unfused"),
                device="cuda:0",
                parameters={
                    "chunk_seconds": 10.0,
                    "max_chunks": 8,
                    "taxonomy": "ezstudio-r3b10",
                },
            ),
            semantic_clap_open_vocab.run,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--audio-hash", required=True)
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--progress-file", required=True)
    args = parser.parse_args()

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
    ai_root, profile_root = _model_roots()

    context = PedalContext(
        source=source,
        audio_sha256=args.audio_hash,
        y=np.asarray(y, dtype=np.float32),
        sr=int(sr),
        model_root=profile_root,
        ai_models_root=ai_root,
    )

    board = build_pedalboard(profile_root)
    pedalboard_result = board.run(
        context,
        progress=lambda percent, message: write_progress(
            progress,
            percent,
            message,
        ),
    )

    characteristics, tagging, warnings = _legacy_projection(
        pedalboard_result,
        duration,
    )

    result = {
        "schema": SCHEMA,
        "audio_sha256": args.audio_hash,
        "source_sha256": sha256(source),
        "characteristics": characteristics,
        "tagging": tagging,
        "pedalboard": {
            **pedalboard_result,
            "ai_models_root": str(ai_root),
            "profile_models_root": str(profile_root),
        },
        "warnings": warnings,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "librosa": getattr(librosa, "__version__", ""),
            "ai_models_root": str(ai_root),
            "profile_models": str(profile_root),
            "profile_semantic_backend": str(tagging.get("backend") or ""),
            "profile_meter_source": str(
                characteristics.get("time_signature", {}).get("source") or ""
            ),
            "profile_architecture": "pedalboard-r3b11",
        },
        "automatic_next_stage": False,
    }

    write_progress(progress, 94, "PROFILE: écriture ADN pedalboard")
    tmp = output.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tmp.replace(output)
    write_progress(progress, 100, "PROFILE terminé")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
