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

from gene import GeneContext, GeneSpec
from gene_registry import GeneRegistry
from genes import descriptors_librosa
from genes import embedding_mert
from genes import meter_chords_shared
from genes import rhythm_librosa
from genes import semantic_clap_open_vocab
from genes import semantic_panns
from genes import semantic_passt
from genes import tonal_ks
from genes import tonal_madmom_key

R3B13_PROFILE_CONSOLIDATION = True
R3B14_PROFILE_REPAIR = True
SCHEMA = "ezstudio.profile.v1"
R3B15B_MADMOM_44100 = True
R3B15_PROFILE_GENES = True
R3B16_PROFILE_CONFIDENCE = True
R3B17_PROFILE_CONFIDENCE_V2 = True
R3B18_PROFILE_CONFIDENCE_V3 = True
R3B19_PROFILE_SEMANTIC_ROLES = True
R3B31_GENOMIC_EVOLUTION = True


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


def _gene_by_id(
    gene_registry_result: dict,
    gene_id: str,
) -> dict | None:
    for record in gene_registry_result.get("genes") or []:
        if record.get("id") == gene_id:
            return record
    return None


def _normalized(record: dict | None) -> dict:
    if not isinstance(record, dict):
        return {}
    value = record.get("normalized")
    return value if isinstance(value, dict) else {}


def _legacy_projection(
    gene_registry_result: dict,
    duration: float,
) -> tuple[dict, dict, list[str]]:
    rhythm = _gene_by_id(gene_registry_result, "rhythm.librosa-beat")
    meter = _gene_by_id(gene_registry_result, "meter.chords-shared-r9")
    tonal_consensus = (
        (gene_registry_result.get("consensus") or {}).get("tonal") or {}
    )
    descriptors = _gene_by_id(
        gene_registry_result,
        "descriptors.librosa-lowlevel",
    )
    clap = _gene_by_id(
        gene_registry_result,
        "semantic.clap-open-vocabulary",
    )

    rhythm_n = _normalized(rhythm)
    meter_n = _normalized(meter)
    descriptors_n = _normalized(descriptors)

    tonal_label = tonal_consensus.get("label")
    tonic = None
    mode = None
    if isinstance(tonal_label, str) and " " in tonal_label:
        tonic, mode = tonal_label.rsplit(" ", 1)

    tonal_n = {
        "label": tonal_label,
        "tonic": tonic,
        "mode": mode,
        "confidence": None,
        "calibrated": False,
        "source": "profile-tonal-consensus-v1",
        "decision": tonal_consensus.get("decision"),
        "candidate_label": tonal_consensus.get("candidate_label"),
        "support": tonal_consensus.get("support"),
        "total_sources": tonal_consensus.get("total_sources"),
        "agreement_ratio": tonal_consensus.get("agreement_ratio"),
        "unanimous": tonal_consensus.get("unanimous"),
        "sources": tonal_consensus.get("sources") or [],
        "dissent": tonal_consensus.get("dissent") or [],
    }

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

    # Compatibility projection: CLAP remains the visible open-vocabulary
    # tagging backend. Scientific truth stays in the independent gene outputs.
    if clap and clap.get("status") == "ok":
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
    for record in gene_registry_result.get("genes") or []:
        warnings.extend(
            str(item) for item in (record.get("warnings") or [])
        )
        if record.get("status") == "error":
            error = record.get("error") or {}
            warnings.append(
                "profile_gene_error:"
                + str(record.get("id"))
                + ":"
                + str(error.get("type") or "")
                + ":"
                + str(error.get("message") or "")
            )

    return characteristics, tagging, warnings



def _profile_view(gene_registry_result: dict) -> dict:
    records = gene_registry_result.get("genes") or []
    consensus = gene_registry_result.get("consensus") or {}

    gene_rows = []
    embeddings = []
    counts = {"ok": 0, "skipped": 0, "error": 0}

    for record in records:
        status = str(record.get("status") or "error")
        counts[status] = counts.get(status, 0) + 1
        error = record.get("error") if isinstance(record.get("error"), dict) else {}
        gene_rows.append(
            {
                "id": record.get("id"),
                "name": record.get("name"),
                "family": record.get("family"),
                "status": status,
                "device": record.get("device"),
                "elapsed_seconds": (record.get("timing") or {}).get("elapsed_seconds"),
                "error": error.get("message"),
                "warnings": list(record.get("warnings") or []),
            }
        )

        if record.get("family") == "embedding":
            normalized = (
                record.get("normalized")
                if isinstance(record.get("normalized"), dict)
                else {}
            )
            raw = record.get("raw") if isinstance(record.get("raw"), dict) else {}
            embeddings.append(
                {
                    "id": record.get("id"),
                    "name": record.get("name"),
                    "status": status,
                    "embedding_norm": normalized.get("embedding_norm"),
                    "temporal_std_mean": normalized.get("temporal_std_mean"),
                    "hidden_size": raw.get("hidden_size"),
                    "chunk_count": raw.get("chunk_count"),
                }
            )

    semantic = consensus.get("semantic") if isinstance(consensus.get("semantic"), dict) else {}
    audioset = semantic.get("audioset") if isinstance(semantic.get("audioset"), dict) else {}

    return {
        "counts": counts,
        "genes": gene_rows,
        "tonal": consensus.get("tonal") or {},
        "audioset": {
            "method": audioset.get("method"),
            "confidence_method": audioset.get("confidence_method"),
            "confidence_threshold": audioset.get("confidence_threshold"),
            "calibrated": bool(audioset.get("calibrated", False)),
            "accepted": list(audioset.get("accepted") or [])[:25],
            "agreements": list(audioset.get("agreements") or [])[:25],
            "divergences": list(audioset.get("divergences") or [])[:25],
        },
        "embeddings": embeddings,
        "policy": consensus.get("policy") or {},
    }


def _model_roots() -> tuple[Path, Path]:
    ai_root = Path(os.getenv("AI_MODELS_ROOT", r"H:\AIModels"))
    profile_root = Path(
        os.getenv(
            "EZSTUDIO_PROFILE_MODELS",
            str(ai_root / "audio" / "profile"),
        )
    )
    return ai_root, profile_root


def build_gene_registry(
    ai_root: Path,
    profile_root: Path,
) -> GeneRegistry:
    return (
        GeneRegistry()
        .add(
            GeneSpec(
                gene_id="rhythm.librosa-beat",
                display_name="Librosa Beat Tracker",
                family="rhythm",
                order=10,
                engine="librosa",
                parameters={
                    "mono": True,
                    "analysis_sample_rate": 22050,
                },
            ),
            rhythm_librosa.run,
        )
        .add(
            GeneSpec(
                gene_id="meter.chords-shared-r9",
                display_name="CHORDS Shared Meter R9",
                family="meter",
                order=20,
                engine="chords_metric_r9",
                model_id="beat-this-final0",
                model_path=str(
                    Path(
                        os.getenv(
                            "EZSTUDIO_BEAT_THIS_CHECKPOINT",
                            str(
                                ai_root
                                / "audio"
                                / "rhythm"
                                / "beat-this"
                                / "beat_this-final0.ckpt"
                            ),
                        )
                    )
                ),
                device="cuda:0",
                thresholds={"confidence": 0.50},
            ),
            meter_chords_shared.run,
        )
        .add(
            GeneSpec(
                gene_id="tonal.krumhansl-schmuckler",
                display_name="Krumhansl-Schmuckler Key",
                family="tonal",
                order=30,
                engine="librosa-chroma-cqt+ks",
                parameters={"chroma": "CQT"},
            ),
            tonal_ks.run,
        )
        .add(
            GeneSpec(
                gene_id="tonal.madmom-key-cnn-2017",
                display_name="Madmom Key CNN 2017 Ensemble",
                family="tonal",
                order=31,
                engine="madmom-infer",
                model_id="CPJKU-key-cnn-2017-ensemble4",
                model_path=str(
                    ai_root
                    / "audio"
                    / "tonal"
                    / "madmom-key-cnn"
                    / "2017"
                ),
                device="cpu:numpy",
            ),
            tonal_madmom_key.run_2017,
        )
        .add(
            GeneSpec(
                gene_id="tonal.madmom-key-cnn-2018",
                display_name="Madmom Genre-Agnostic Key CNN 2018",
                family="tonal",
                order=32,
                engine="madmom-infer",
                model_id="CPJKU-key-cnn-2018",
                model_path=str(
                    ai_root
                    / "audio"
                    / "tonal"
                    / "madmom-key-cnn"
                    / "2018"
                    / "key_cnn.pkl"
                ),
                device="cpu:numpy",
            ),
            tonal_madmom_key.run_2018,
        )
        .add(
            GeneSpec(
                gene_id="descriptors.librosa-lowlevel",
                display_name="Librosa Low-Level Descriptors",
                family="descriptors",
                order=40,
                engine="librosa",
                parameters={"rolloff_percent": 0.85},
            ),
            descriptors_librosa.run,
        )
        .add(
            GeneSpec(
                gene_id="semantic.clap-open-vocabulary",
                display_name="CLAP Open Vocabulary",
                family="semantic",
                order=60,
                engine="transformers.CLAP",
                model_id="laion/clap-htsat-unfused",
                model_path=str(
                    profile_root / "clap-htsat-unfused"
                ),
                device="cuda:0",
                parameters={
                    "chunk_seconds": 10.0,
                    "max_chunks": 8,
                    "taxonomy": "ezstudio-r3b10",
                },
            ),
            semantic_clap_open_vocab.run,
        )
        .add(
            GeneSpec(
                gene_id="embedding.mert-95m",
                display_name="MERT Music Embedding 95M",
                family="embedding",
                order=70,
                engine="transformers.MERT",
                model_id="m-a-p/MERT-v1-95M",
                model_path=str(
                    ai_root
                    / "audio"
                    / "embeddings"
                    / "mert"
                    / "MERT-v1-95M"
                ),
                device="cuda:0",
                parameters={
                    "chunk_seconds": 10.0,
                    "max_chunks": 6,
                    "aggregation": "mean",
                    "dtype": "float16",
                },
            ),
            embedding_mert.run_95m,
        )
        .add(
            GeneSpec(
                gene_id="embedding.mert-330m",
                display_name="MERT Music Embedding 330M",
                family="embedding",
                order=71,
                engine="transformers.MERT",
                model_id="m-a-p/MERT-v1-330M",
                model_path=str(
                    ai_root
                    / "audio"
                    / "embeddings"
                    / "mert"
                    / "MERT-v1-330M"
                ),
                device="cuda:0",
                parameters={
                    "chunk_seconds": 10.0,
                    "max_chunks": 6,
                    "aggregation": "mean",
                    "dtype": "float16",
                },
            ),
            embedding_mert.run_330m,
        )
        .add(
            GeneSpec(
                gene_id="semantic.panns-cnn14",
                display_name="PANNs CNN14 AudioSet",
                family="semantic",
                order=80,
                engine="panns-inference",
                model_id="Cnn14_mAP=0.431",
                model_path=str(
                    ai_root
                    / "audio"
                    / "semantic"
                    / "panns"
                    / "Cnn14_mAP=0.431.pth"
                ),
                device="cuda:0",
                parameters={
                    "sample_rate": 32000,
                    "chunk_seconds": 10.0,
                    "max_chunks": 8,
                },
            ),
            semantic_panns.run,
        )
        .add(
            GeneSpec(
                gene_id="semantic.passt-audioset",
                display_name="PaSST AudioSet Transformer",
                family="semantic",
                order=81,
                engine="hear21passt",
                model_id="passt_s_swa_p16_128_ap476",
                model_path=str(
                    ai_root
                    / "audio"
                    / "semantic"
                    / "passt"
                    / "passt-s-f128-p16-s10-ap.476-swa.pt"
                ),
                device="cuda:0",
                parameters={
                    "sample_rate": 32000,
                    "chunk_seconds": 10.0,
                    "max_chunks": 8,
                },
            ),
            semantic_passt.run,
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
    os.environ["EZSTUDIO_PROFILE_OBSERVABILITY_SESSION"] = output.parent.name
    output.parent.mkdir(parents=True, exist_ok=True)

    write_progress(progress, 3, "PROFILE: chargement")
    import librosa

    y, sr = librosa.load(str(source), sr=22050, mono=True)
    if y.size == 0:
        raise RuntimeError("profile_audio_empty")

    duration = float(librosa.get_duration(y=y, sr=sr))
    ai_root, profile_root = _model_roots()

    context = GeneContext(
        source=source,
        audio_sha256=args.audio_hash,
        y=np.asarray(y, dtype=np.float32),
        sr=int(sr),
        model_root=profile_root,
        ai_models_root=ai_root,
    )

    registry = build_gene_registry(ai_root, profile_root)
    gene_registry_result = registry.run(
        context,
        progress=lambda percent, message: write_progress(
            progress,
            percent,
            message,
        ),
    )
    genome_manifest = registry.genome_manifest(
        gene_registry_result.get("genes") or [],
    )

    characteristics, tagging, warnings = _legacy_projection(
        gene_registry_result,
        duration,
    )
    profile_view = _profile_view(gene_registry_result)

    result = {
        "schema": SCHEMA,
        "audio_sha256": args.audio_hash,
        "source_sha256": sha256(source),
        "characteristics": characteristics,
        "tagging": tagging,
        "profile_view": profile_view,
        "gene_registry": {
            **gene_registry_result,
            "ai_models_root": str(ai_root),
            "profile_models_root": str(profile_root),
        },
        "genome": genome_manifest,
        "warnings": warnings,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "librosa": getattr(librosa, "__version__", ""),
            "ai_models_root": str(ai_root),
            "profile_models": str(profile_root),
            "profile_semantic_backend": str(
                tagging.get("backend") or ""
            ),
            "profile_meter_source": str(
                characteristics
                .get("time_signature", {})
                .get("source")
                or ""
            ),
            "profile_architecture": "genes-r3b31-genomic-evolution",
            "profile_dependency_root": os.getenv(
                "EZSTUDIO_PROFILE_DEP_ROOT",
                r"H:\EZStudio_lab\var\runtime\deps\profile-r3b12",
            ),
        },
        "automatic_next_stage": False,
    }

    write_progress(progress, 96, "PROFILE: écriture ADN R3B31")
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
