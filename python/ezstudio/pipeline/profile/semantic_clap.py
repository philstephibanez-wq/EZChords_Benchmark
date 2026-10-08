from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np

MODEL_NAME = "laion/clap-htsat-unfused"

TAXONOMY = {
    "genre": [
        "chanson française", "folk", "ballad", "singer-songwriter",
        "pop", "rock", "soft rock", "jazz", "blues", "soul",
        "classical", "orchestral", "country", "electronic",
        "disco", "funk", "reggae", "latin", "world music", "cabaret",
    ],
    "instrumentation": [
        "acoustic guitar", "electric guitar", "piano", "accordion",
        "violin", "cello", "string section", "acoustic bass",
        "bass guitar", "drum kit", "percussion", "snare drum",
        "kick drum", "organ", "synthesizer", "brass section",
        "trumpet", "trombone", "saxophone", "flute", "clarinet",
        "harmonica", "mandolin", "ukulele", "harp",
    ],
    "mood": [
        "emotional", "reflective", "intimate", "somber", "passionate",
        "mournful", "longing", "dramatic", "romantic", "melancholic",
        "warm", "calm", "dreamy", "nostalgic", "dark", "tense",
        "energetic", "joyful", "uplifting", "peaceful",
    ],
    "voice": [
        "male lead vocal", "female lead vocal", "backing vocals",
        "vocal harmonies", "choir", "spoken voice",
        "raspy singing voice", "vibrato singing",
        "powerful emotional singing", "soft intimate singing",
        "instrumental music with no vocals",
    ],
}


def _dependency_root() -> Path:
    return Path(
        os.getenv(
            "EZSTUDIO_PROFILE_DEP_ROOT",
            r"H:\temp\EZStudio_lab\deps\profile-r3b10",
        )
    )


def _model_dir(model_root: Path) -> Path:
    return model_root / "clap-htsat-unfused"


def _prepare_imports() -> None:
    dep_root = _dependency_root()
    if dep_root.is_dir() and str(dep_root) not in sys.path:
        # Append: keep validated LAB numpy/librosa/torch ahead of this root.
        sys.path.append(str(dep_root))


def _prompts() -> tuple[list[str], list[tuple[str, str]]]:
    prompts: list[str] = []
    index: list[tuple[str, str]] = []

    templates = {
        "genre": "This music is {label}.",
        "instrumentation": "This music contains {label}.",
        "mood": "The mood of this music is {label}.",
        "voice": "The recording features {label}.",
    }

    for family, labels in TAXONOMY.items():
        for label in labels:
            prompts.append(templates[family].format(label=label))
            index.append((family, label))

    return prompts, index


def _even_chunks(
    y: np.ndarray,
    sr: int,
    *,
    chunk_seconds: float = 10.0,
    max_chunks: int = 8,
) -> list[np.ndarray]:
    y = np.asarray(y, dtype=np.float32)
    chunk = max(1, int(round(chunk_seconds * sr)))

    if len(y) <= chunk:
        padded = np.zeros(chunk, dtype=np.float32)
        padded[: len(y)] = y
        return [padded]

    max_start = len(y) - chunk
    starts = np.linspace(0, max_start, num=max_chunks, dtype=int)
    return [y[int(start): int(start) + chunk] for start in starts]


def _family_scores(
    logits: np.ndarray,
    index: list[tuple[str, str]],
    family: str,
    top_n: int,
) -> list[dict]:
    positions = [i for i, item in enumerate(index) if item[0] == family]
    if not positions:
        return []

    values = np.asarray([logits[i] for i in positions], dtype=np.float64)
    values = values - np.max(values)
    probs = np.exp(values)
    probs /= np.sum(probs) + 1e-12

    order = np.argsort(probs)[::-1][:top_n]
    rows = []
    for relative_index in order:
        absolute_index = positions[int(relative_index)]
        label = index[absolute_index][1]
        rows.append({
            "label": label,
            "score": round(float(probs[int(relative_index)]), 4),
            "score_type": "category_relative_softmax",
        })
    return rows


def clap_tags(source: Path, model_root: Path) -> tuple[dict, list[str]]:
    result = {
        "available": False,
        "backend": "clap-zero-shot",
        "model": MODEL_NAME,
        "genre": [],
        "instrumentation": [],
        "mood": [],
        "voice": [],
        "score_semantics": "relative within each configured taxonomy",
    }
    warnings: list[str] = []

    _prepare_imports()

    model_dir = _model_dir(model_root)
    if not model_dir.is_dir():
        warnings.append(f"profile_clap_model_missing:{model_dir}")
        return result, warnings

    try:
        import librosa
        import torch
        from transformers import ClapModel, ClapProcessor
    except Exception as exc:
        warnings.append(
            f"profile_clap_dependency_unavailable:{type(exc).__name__}:{exc}"
        )
        return result, warnings

    if not torch.cuda.is_available():
        warnings.append("profile_clap_cuda_required")
        return result, warnings

    try:
        processor = ClapProcessor.from_pretrained(
            str(model_dir),
            local_files_only=True,
        )
        model = ClapModel.from_pretrained(
            str(model_dir),
            local_files_only=True,
        ).to("cuda")
        model.eval()

        y, sr = librosa.load(str(source), sr=48000, mono=True)
        chunks = _even_chunks(y, sr)

        prompts, index = _prompts()
        accumulated = None

        with torch.inference_mode():
            for chunk in chunks:
                inputs = processor(
                    text=prompts,
                    audios=chunk,
                    sampling_rate=sr,
                    return_tensors="pt",
                    padding=True,
                )
                inputs = {
                    key: value.to("cuda") if hasattr(value, "to") else value
                    for key, value in inputs.items()
                }
                output = model(**inputs)
                logits = (
                    output.logits_per_audio.detach().float().cpu().numpy()[0]
                )
                accumulated = logits if accumulated is None else accumulated + logits

        if accumulated is None:
            warnings.append("profile_clap_no_audio_chunks")
            return result, warnings

        mean_logits = accumulated / float(len(chunks))

        result["genre"] = _family_scores(mean_logits, index, "genre", 6)
        result["instrumentation"] = _family_scores(
            mean_logits, index, "instrumentation", 12
        )
        result["mood"] = _family_scores(mean_logits, index, "mood", 8)
        result["voice"] = _family_scores(mean_logits, index, "voice", 8)
        result["available"] = True
        result["chunks"] = len(chunks)
        result["chunk_seconds"] = 10.0

        try:
            import transformers
            result["transformers_version"] = transformers.__version__
        except Exception:
            pass

        return result, warnings

    except Exception as exc:
        warnings.append(
            f"profile_clap_inference_error:{type(exc).__name__}:{exc}"
        )
        return result, warnings
