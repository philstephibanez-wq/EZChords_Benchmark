from __future__ import annotations

from collections import defaultdict
import math
from typing import Any, Callable

from gene import ModuleContext, ModuleConfig, run_module
from canonical_profile import build_genre_hierarchy, build_vocal_profile


class ModuleRegistry:
    def __init__(self) -> None:
        self._entries: list[
            tuple[ModuleConfig, Callable[[ModuleContext], dict[str, Any]]]
        ] = []

    def add(
        self,
        spec: ModuleConfig,
        fn: Callable[[ModuleContext], dict[str, Any]],
    ) -> "ModuleRegistry":
        self._entries.append((spec, fn))
        return self

    def genome_manifest(
        self,
        records: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        import hashlib
        import inspect
        from pathlib import Path

        by_id = {
            str(record.get("id")): record
            for record in (records or [])
        }
        genes = []

        for spec, fn in sorted(
            self._entries,
            key=lambda item: item[0].order,
        ):
            runtime = by_id.get(spec.module_id, {})
            source_file = inspect.getsourcefile(fn)
            source_sha256 = None
            if source_file and Path(source_file).is_file():
                h = hashlib.sha256()
                with Path(source_file).open("rb") as handle:
                    for chunk in iter(
                        lambda: handle.read(1024 * 1024),
                        b"",
                    ):
                        h.update(chunk)
                source_sha256 = h.hexdigest()

            engine = {
                "name": spec.engine,
                "version": spec.engine_version,
            }
            if isinstance(runtime.get("engine"), dict):
                engine.update(runtime["engine"])

            model = {
                "id": spec.model_id,
                "path": spec.model_path,
            }
            if isinstance(runtime.get("model"), dict):
                model.update(runtime["model"])

            genes.append(
                {
                    "id": spec.module_id,
                    "name": spec.display_name,
                    "family": spec.family,
                    "order": spec.order,
                    "engine": engine,
                    "model": model,
                    "device": runtime.get("device") or spec.device,
                    "parameters": spec.parameters,
                    "thresholds": spec.thresholds,
                    "weights": spec.weights,
                    "implementation": {
                        "callable": f"{fn.__module__}.{fn.__qualname__}",
                        "source_sha256": source_sha256,
                    },
                }
            )

        return {
            "schema": "ezstudio.genome.region.v1",
            "region": "profile",
            "pipeline_revision": "profile-r3b35c-canonical-genre-vocals",
            "genes": genes,
        }

    def run(
        self,
        context: ModuleContext,
        progress: Callable[[int, str], None] | None = None,
    ) -> dict[str, Any]:
        entries = sorted(self._entries, key=lambda item: item[0].order)
        records: list[dict[str, Any]] = []
        total = max(1, len(entries))

        for index, (spec, fn) in enumerate(entries):
            if progress:
                percent = 8 + int((index / total) * 84)
                progress(percent, f"PROFILE: {spec.display_name}")
            records.append(run_module(spec, context, fn))

        by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            by_family[str(record.get("family") or "unknown")].append(record)

        return {
            "schema": "ezstudio.profile.genes.v1",
            "genes": records,
            "families": dict(by_family),
            "consensus": build_consensus(records),
        }


def _semantic_rows(
    record: dict[str, Any],
    family: str,
) -> list[dict[str, Any]]:
    normalized = record.get("normalized")
    if not isinstance(normalized, dict):
        return []
    rows = normalized.get(family)
    return rows if isinstance(rows, list) else []


def _temporal_row(
    record: dict[str, Any],
    family: str,
    label: str,
) -> dict[str, Any]:
    raw = record.get("raw")
    if not isinstance(raw, dict):
        return {}
    temporal = raw.get("temporal")
    if not isinstance(temporal, dict):
        return {}
    family_rows = temporal.get(family)
    if not isinstance(family_rows, dict):
        return {}

    direct = family_rows.get(label)
    if isinstance(direct, dict):
        return direct

    wanted = label.casefold()
    for key, value in family_rows.items():
        if str(key).casefold() == wanted and isinstance(value, dict):
            return value
    return {}



_INSTRUMENT_CANONICAL = {
    "acoustic guitar": "acoustic guitar",
    "electric guitar": "electric guitar",
    "guitar": "guitar",
    "bass guitar": "bass guitar",
    "acoustic bass": "acoustic bass",
    "double bass": "acoustic bass",
    "piano": "piano",
    "electric piano": "electric piano",
    "organ": "organ",
    "electronic organ": "organ",
    "synthesizer": "synthesizer",
    "synthesizer keyboard": "synthesizer",
    "drum kit": "drum kit",
    "drums": "drum kit",
    "snare drum": "snare drum",
    "bass drum": "kick drum",
    "kick drum": "kick drum",
    "cymbal": "cymbal",
    "percussion": "percussion",
    "violin": "violin",
    "fiddle": "violin",
    "cello": "cello",
    "string section": "string section",
    "brass instrument": "brass section",
    "brass section": "brass section",
    "trumpet": "trumpet",
    "trombone": "trombone",
    "saxophone": "saxophone",
    "flute": "flute",
    "clarinet": "clarinet",
    "harmonica": "harmonica",
    "accordion": "accordion",
    "harp": "harp",
    "mandolin": "mandolin",
    "ukulele": "ukulele",
    "keyboard (musical)": "keyboard",
    "keyboard": "keyboard",
}


def _canonical_instrument(label: str) -> str | None:
    key = " ".join(str(label).casefold().replace("_", " ").split())
    if key in _INSTRUMENT_CANONICAL:
        return _INSTRUMENT_CANONICAL[key]
    return None


def _build_instrumentation_consensus(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Cross-engine instrumentation evidence, intentionally uncalibrated.

    CLAP supplies open-vocabulary instrument hypotheses. PANNs and PaSST
    supply AudioSet labels. We canonicalize only exact known instrument labels,
    preserve each source/rank, and require support from >=2 engines for a
    candidate. This is an experimental PROFILE output until human benchmarking
    proves it reliable enough for STEMS.
    """
    evidence: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_gene_label: set[tuple[str, str]] = set()

    for record in records:
        if record.get("status") != "ok":
            continue
        gene_id = str(record.get("id") or "")

        if gene_id == "semantic.clap-open-vocabulary":
            rows = _semantic_rows(record, "instrumentation")[:6]
            source_family = "clap_instrumentation"
        elif gene_id in {"semantic.panns-cnn14", "semantic.passt-audioset"}:
            rows = _semantic_rows(record, "audioset")[:25]
            source_family = "audioset"
        else:
            continue

        for rank, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                continue
            source_label = str(row.get("label") or "").strip()
            canonical = _canonical_instrument(source_label)
            if canonical is None:
                continue
            dedupe = (gene_id, canonical)
            if dedupe in seen_gene_label:
                continue
            seen_gene_label.add(dedupe)

            temporal = _temporal_row(record, "audioset", source_label)
            evidence[canonical].append(
                {
                    "gene": gene_id,
                    "source_family": source_family,
                    "source_label": source_label,
                    "rank": rank,
                    "raw_score": round(float(row.get("score") or 0.0), 6),
                    "top5_support": temporal.get("top5_support"),
                    "top10_support": temporal.get("top10_support"),
                }
            )

    rows: list[dict[str, Any]] = []
    for label, sources in evidence.items():
        support = len({str(item["gene"]) for item in sources})
        reciprocal_rank = sum(
            1.0 / max(1, int(item["rank"]))
            for item in sources
        ) / max(1, len(sources))
        rows.append(
            {
                "label": label,
                "support": support,
                "source_count": len(sources),
                "rank_consensus": round(reciprocal_rank, 6),
                "sources": sources,
                "decision": "candidate" if support >= 2 else "weak",
            }
        )

    rows.sort(
        key=lambda row: (
            -int(row["support"]),
            -float(row["rank_consensus"]),
            str(row["label"]),
        )
    )
    candidates = [row for row in rows if row["decision"] == "candidate"]
    weak = [row for row in rows if row["decision"] == "weak"]

    return {
        "schema": "ezstudio.profile.instrumentation-consensus.v1",
        "status": "experimental",
        "method": "canonical-label-rank-support-v1",
        "calibrated": False,
        "usable_for_stems": False,
        "candidate_min_engine_support": 2,
        "candidates": candidates[:12],
        "weak": weak[:20],
        "abstain": len(candidates) == 0,
        "note": (
            "Experimental mix-level instrumentation. No calibrated probability; "
            "STEMS use is forbidden until the human benchmark gate passes."
        ),
    }



_CHOIR_CLAP_LABELS = {
    "choir",
    "backing vocals",
    "vocal harmonies",
}
_CHOIR_AUDIOSET_LABELS = {
    "choir",
    "chant",
    "a capella",
    "vocal music",
}


def _full_audioset_rank(
    record: dict[str, Any],
    wanted: set[str],
) -> dict[str, Any] | None:
    raw = record.get("raw")
    if not isinstance(raw, dict):
        return None
    scores = raw.get("audioset_scores")
    if not isinstance(scores, dict) or not scores:
        return None

    ranked: list[tuple[str, float]] = []
    for label, value in scores.items():
        try:
            ranked.append((str(label), float(value)))
        except (TypeError, ValueError):
            continue
    ranked.sort(key=lambda item: item[1], reverse=True)

    best = None
    for rank, (label, score) in enumerate(ranked, start=1):
        if label.casefold() not in wanted:
            continue
        row = {
            "label": label,
            "score": round(score, 6),
            "rank": rank,
            "class_count": len(ranked),
        }
        if best is None or rank < int(best["rank"]):
            best = row
    return best


def _build_choir_consensus(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    # Conservative mix-level choir/backing-vocals evidence.
    # Absence of a choir-specific label is never converted into a negative assertion.
    sources: list[dict[str, Any]] = []

    for record in records:
        if record.get("status") != "ok":
            continue
        gene_id = str(record.get("id") or "")

        if gene_id == "semantic.clap-open-vocabulary":
            rows = _semantic_rows(record, "voice")
            best = None
            for rank, row in enumerate(rows, start=1):
                if not isinstance(row, dict):
                    continue
                label = str(row.get("label") or "").strip()
                if label.casefold() not in _CHOIR_CLAP_LABELS:
                    continue
                try:
                    score = float(row.get("score") or 0.0)
                except (TypeError, ValueError):
                    score = 0.0
                candidate = {
                    "gene": gene_id,
                    "label": label,
                    "score": round(score, 6),
                    "rank": rank,
                    "evidence": (
                        "strong"
                        if rank <= 3 and score >= 0.10
                        else "weak"
                    ),
                }
                if best is None or rank < int(best["rank"]):
                    best = candidate
            if best is not None:
                sources.append(best)

        elif gene_id in {
            "semantic.panns-cnn14",
            "semantic.passt-audioset",
        }:
            best = _full_audioset_rank(
                record,
                _CHOIR_AUDIOSET_LABELS,
            )
            if best is not None:
                rank = int(best["rank"])
                score = float(best["score"])
                sources.append(
                    {
                        "gene": gene_id,
                        "label": best["label"],
                        "score": round(score, 6),
                        "rank": rank,
                        "class_count": best["class_count"],
                        "evidence": (
                            "strong"
                            if rank <= 12
                            else (
                                "weak"
                                if rank <= 25
                                else "trace"
                            )
                        ),
                    }
                )

    strong_genes = {
        str(row["gene"])
        for row in sources
        if row.get("evidence") == "strong"
    }
    weak_or_better = {
        str(row["gene"])
        for row in sources
        if row.get("evidence") in {"strong", "weak"}
    }

    if len(strong_genes) >= 2:
        decision = "detected"
    elif len(strong_genes) >= 1 or len(weak_or_better) >= 2:
        decision = "possible"
    else:
        decision = "inconclusive"

    return {
        "schema": "ezstudio.profile.choirs-consensus.v1",
        "status": "experimental",
        "decision": decision,
        "calibrated": False,
        "usable_for_stems": False,
        "sources": sources,
        "strong_engine_support": len(strong_genes),
        "weak_or_better_engine_support": len(weak_or_better),
        "abstain": decision == "inconclusive",
        "note": (
            "Conservative pre-STEMS choir/backing-vocals evidence. "
            "Inconclusive means machine abstention, never confirmed absence."
        ),
    }


def build_consensus(records: list[dict[str, Any]]) -> dict[str, Any]:
    semantic_records = [
        record
        for record in records
        if record.get("family") == "semantic"
        and record.get("status") == "ok"
    ]

    semantic_by_id = {
        str(record.get("id")): record
        for record in semantic_records
    }

    semantic: dict[str, Any] = {}
    for family in (
        "genre",
        "instrumentation",
        "mood",
        "voice",
        "audioset",
    ):
        support: dict[str, list[dict[str, Any]]] = defaultdict(list)
        per_engine: dict[str, list[dict[str, Any]]] = {}

        for record in semantic_records:
            rows = _semantic_rows(record, family)
            if not rows:
                continue
            per_engine[str(record["id"])] = rows
            for row in rows:
                if not isinstance(row, dict):
                    continue
                label = str(row.get("label") or "").strip()
                if not label:
                    continue
                try:
                    score = float(row.get("score") or 0.0)
                except (TypeError, ValueError):
                    score = 0.0
                support[label.casefold()].append(
                    {
                        "label": label,
                        "score": score,
                        "gene": record["id"],
                    }
                )

        agreements = []
        divergences = []
        for items in support.values():
            canonical = items[0]["label"]
            row = {
                "label": canonical,
                "support": len(items),
                "sources": [
                    {
                        "gene": item["gene"],
                        "score": round(float(item["score"]), 6),
                    }
                    for item in items
                ],
            }

            if family == "audioset" and len(items) >= 2:
                source_evidence = []
                for item in items:
                    source_record = semantic_by_id.get(str(item["gene"]))
                    if not isinstance(source_record, dict):
                        continue
                    temporal = _temporal_row(
                        source_record,
                        family,
                        canonical,
                    )
                    rank = temporal.get("rank")
                    top5_support = temporal.get("top5_support")
                    top10_support = temporal.get("top10_support")
                    if (
                        rank is None
                        or top5_support is None
                        or top10_support is None
                    ):
                        continue

                    rank_value = max(1, int(rank))
                    top5 = max(0.0, min(1.0, float(top5_support)))
                    top10 = max(0.0, min(1.0, float(top10_support)))

                    rank_score = math.exp(
                        -math.log(2.0)
                        * float(rank_value - 1)
                        / 9.0
                    )
                    temporal_score = math.sqrt(top5 * top10)
                    engine_confidence = math.sqrt(
                        rank_score * temporal_score
                    )

                    source_evidence.append(
                        {
                            "gene": item["gene"],
                            "raw_score": round(float(item["score"]), 6),
                            "rank": rank_value,
                            "class_count": temporal.get("class_count"),
                            "rank_score": round(rank_score, 6),
                            "top5_support": round(top5, 6),
                            "top10_support": round(top10, 6),
                            "temporal_score": round(temporal_score, 6),
                            "engine_confidence": round(
                                engine_confidence,
                                6,
                            ),
                        }
                    )

                confidence = (
                    min(
                        float(item["engine_confidence"])
                        for item in source_evidence
                    )
                    if len(source_evidence) == len(items)
                    else None
                )

                normalized_label = canonical.casefold()
                generic_labels = {
                    "music",
                    "musical instrument",
                    "song",
                }
                contextual_labels = {
                    "christian music",
                    "christmas music",
                    "gospel music",
                }

                if normalized_label in generic_labels:
                    semantic_role = "generic"
                elif normalized_label in contextual_labels:
                    semantic_role = "contextual_style"
                else:
                    semantic_role = "audioset_evidence"

                informative = semantic_role == "audioset_evidence"
                accepted = (
                    informative
                    and confidence is not None
                    and confidence >= 0.60
                )

                row.update(
                    {
                        "confidence": (
                            round(confidence, 6)
                            if confidence is not None
                            else None
                        ),
                        "confidence_method": (
                            "min-cross-model-geomean"
                            "(absolute-rank-decay,"
                            "top5-top10-temporal)-v3"
                        ),
                        "confidence_threshold": 0.60,
                        "calibrated": False,
                        "semantic_role": semantic_role,
                        "informative": informative,
                        "source_evidence": source_evidence,
                        "decision": (
                            "accepted"
                            if accepted
                            else (
                                "generic"
                                if semantic_role == "generic"
                                else (
                                    "contextual"
                                    if semantic_role == "contextual_style"
                                    else "uncertain"
                                )
                            )
                        ),
                    }
                )

            if len(items) >= 2:
                agreements.append(row)
            else:
                divergences.append(row)

        agreements.sort(
            key=lambda row: (-int(row["support"]), str(row["label"]).casefold())
        )
        divergences.sort(
            key=lambda row: str(row["label"]).casefold()
        )

        if per_engine:
            payload = {
                "method": (
                    "exact-label-agreement-"
                    "no-cross-engine-score-calibration"
                ),
                "agreements": agreements,
                "divergences": divergences,
                "per_engine": per_engine,
            }
            if family == "audioset":
                payload.update(
                    {
                        "confidence_method": (
                            "min-cross-model-geomean"
                            "(absolute-rank-decay,"
                            "top5-top10-temporal)-v3"
                        ),
                        "confidence_threshold": 0.60,
                        "calibrated": False,
                        "accepted": [
                            row
                            for row in agreements
                            if row.get("decision") == "accepted"
                        ],
                    }
                )
            semantic[family] = payload

    tonal_records = [
        record
        for record in records
        if record.get("family") == "tonal"
        and record.get("status") == "ok"
    ]
    labels = []
    for record in tonal_records:
        normalized = record.get("normalized")
        if isinstance(normalized, dict) and normalized.get("label"):
            calibrated = (
                record.get("calibrated")
                if isinstance(record.get("calibrated"), dict)
                else {}
            )
            labels.append(
                {
                    "gene": record["id"],
                    "label": normalized.get("label"),
                    "confidence": normalized.get("confidence"),
                    "margin": normalized.get("margin"),
                    "temporal_stability": normalized.get(
                        "temporal_stability"
                    ),
                    "calibration_status": calibrated.get("status"),
                    "calibration_method": calibrated.get("method"),
                }
            )

    tonal: dict[str, Any] = {}
    if labels:
        counts: dict[str, int] = defaultdict(int)
        for item in labels:
            counts[str(item["label"])] += 1

        ranked = sorted(
            counts.items(),
            key=lambda pair: (-pair[1], pair[0].casefold()),
        )
        candidate_label, support = ranked[0]
        total_sources = len(labels)
        accepted = support >= 2
        dissent = [
            item
            for item in labels
            if str(item["label"]) != candidate_label
        ]

        tonal = {
            "method": "majority-vote-preserving-source-evidence-v1",
            "decision": "accepted" if accepted else "ambiguous",
            "label": candidate_label if accepted else None,
            "candidate_label": candidate_label,
            "support": support,
            "total_sources": total_sources,
            "agreement_ratio": round(
                support / float(total_sources),
                6,
            ),
            "sources": labels,
            "dissent": dissent,
            "unanimous": support == total_sources,
            "calibrated": False,
            "confidence": None,
            "confidence_note": (
                "No calibrated cross-gene tonal probability yet; "
                "source confidences/margins and dissent are preserved."
            ),
        }

    embedding_records = [
        record
        for record in records
        if record.get("family") == "embedding"
        and record.get("status") == "ok"
    ]

    instrumentation = _build_instrumentation_consensus(records)
    choirs = _build_choir_consensus(records)

    return {
        "semantic": semantic,
        "genre_hierarchy": build_genre_hierarchy(semantic),
        "vocal_profile": build_vocal_profile(semantic),
        "instrumentation": instrumentation,
        "choirs": choirs,
        "tonal": tonal,
        "embedding": {
            "policy": "preserve-each-representation-no-vector-fusion",
            "sources": [
                {
                    "gene": record["id"],
                    "model": (record.get("model") or {}).get("id"),
                    "normalized": record.get("normalized"),
                }
                for record in embedding_records
            ],
        },
        "policy": {
            "cross_engine_scores_are_not_assumed_calibrated": True,
            "raw_and_normalized_outputs_are_preserved": True,
            "divergence_is_preserved": True,
            "embedding_vectors_are_not_averaged_across_models": True,
            "confidence_is_not_calibrated_probability": True,
            "semantic_acceptance_threshold": 0.60,
            "instrumentation_status": "experimental",
            "instrumentation_usable_for_stems": False,
            "choirs_status": "experimental",
            "choirs_usable_for_stems": False,
        },
    }


# Legacy alias retained for terminology-migration compatibility.
GeneRegistry = ModuleRegistry
