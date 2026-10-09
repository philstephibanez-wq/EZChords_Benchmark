from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from pedal import PedalContext, file_sha256
from runtime_deps import prepare_profile_imports


def _ensure_cached_checkpoint(
    checkpoint: Path,
    torch_home: Path,
) -> Path:
    target_dir = torch_home / "hub" / "checkpoints"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "passt-s-f128-p16-s10-ap.476-swa.pt"

    if target.is_file() and target.stat().st_size == checkpoint.stat().st_size:
        return target

    if target.exists():
        target.unlink()

    try:
        os.link(checkpoint, target)
    except OSError:
        shutil.copy2(checkpoint, target)

    return target


def run(context: PedalContext) -> dict:
    prepare_profile_imports()

    try:
        import librosa
        from panns_inference import labels
    except Exception as exc:
        raise RuntimeError(
            f"passt_parent_dependency_unavailable:{type(exc).__name__}:{exc}"
        ) from exc

    passt_python = Path(
        os.getenv(
            "EZSTUDIO_PASST_PYTHON",
            r"H:\EZStudio_lab\var\runtime\venvs\passt-r3b12\Scripts\python.exe",
        )
    )
    if not passt_python.is_file():
        raise RuntimeError(f"passt_isolated_python_missing:{passt_python}")

    checkpoint = (
        context.ai_models_root
        / "audio"
        / "semantic"
        / "passt"
        / "passt-s-f128-p16-s10-ap.476-swa.pt"
    )
    if not checkpoint.is_file():
        raise RuntimeError(f"passt_checkpoint_missing:{checkpoint}")

    torch_home = Path(
        os.getenv(
            "EZSTUDIO_PASST_TORCH_HOME",
            r"H:\EZStudio_lab\var\runtime\cache\passt-torch-home",
        )
    )
    cached = _ensure_cached_checkpoint(checkpoint, torch_home)

    audio = librosa.resample(
        np.asarray(context.y, dtype=np.float32),
        orig_sr=context.sr,
        target_sr=32000,
    ).astype(np.float32, copy=False)

    worker = Path(__file__).resolve().parents[1] / "passt_worker.py"
    if not worker.is_file():
        raise RuntimeError(f"passt_worker_missing:{worker}")

    tmp_root = Path(
        os.getenv(
            "EZSTUDIO_TMP_ROOT",
            r"H:\EZStudio_lab\var\tmp",
        )
    )
    scratch = tmp_root / "profile" / "passt"
    scratch.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix="r3b12-passt-",
        dir=str(scratch),
    ) as tmp_dir:
        tmp = Path(tmp_dir)
        audio_path = tmp / "audio.f32"
        output_path = tmp / "result.json"
        audio_path.write_bytes(audio.tobytes(order="C"))

        command = [
            str(passt_python),
            str(worker),
            "--audio-f32",
            str(audio_path),
            "--checkpoint",
            str(checkpoint),
            "--output",
            str(output_path),
            "--torch-home",
            str(torch_home),
        ]
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if completed.returncode != 0:
            message = (
                (completed.stderr or "").strip()
                or (completed.stdout or "").strip()
                or f"exit={completed.returncode}"
            )
            raise RuntimeError("passt_subprocess_failed:" + message[-4000:])

        child = json.loads(output_path.read_text(encoding="utf-8"))

    scores = np.asarray(child.get("scores") or [], dtype=np.float64)
    label_list = [str(item) for item in labels]
    if scores.size != len(label_list):
        raise RuntimeError(
            f"passt_unexpected_scores:{scores.size}:labels={len(label_list)}"
        )

    order = np.argsort(scores)[::-1]
    top = [
        {
            "label": label_list[int(index)],
            "score": round(float(scores[int(index)]), 6),
            "score_type": "isolated_cuda_sigmoid_mean",
        }
        for index in order[:25]
    ]

    return {
        "raw": {
            "audioset_scores": {
                label_list[index]: round(float(scores[index]), 8)
                for index in range(len(scores))
            },
            "chunk_count": int(child.get("chunk_count") or 0),
            "chunk_seconds": float(child.get("chunk_seconds") or 10.0),
            "isolated_runtime": {
                "python": str(passt_python),
                "torch": child.get("torch"),
                "torchaudio": child.get("torchaudio"),
                "hear21passt": child.get("hear21passt"),
                "cuda": child.get("cuda"),
                "device_name": child.get("device_name"),
            },
            "cache_checkpoint": str(cached),
        },
        "normalized": {
            "audioset": top,
        },
        "model": {
            "id": "PaSST-s-f128-p16-s10-ap476-swa",
            "path": str(checkpoint),
            "sha256": file_sha256(checkpoint),
        },
        "engine": {
            "version": child.get("hear21passt"),
        },
        "device": "cuda:0-isolated",
    }
