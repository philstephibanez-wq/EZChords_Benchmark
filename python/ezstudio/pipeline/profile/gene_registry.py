from __future__ import annotations

from collections import defaultdict
import math
from typing import Any, Callable

from gene import GeneContext, GeneSpec, run_gene


class GeneRegistry:
    def __init__(self) -> None:
        self._entries: list[
            tuple[GeneSpec, Callable[[GeneContext], dict[str, Any]]]
        ] = []

    def add(
        self,
        spec: GeneSpec,
        fn: Callable[[GeneContext], dict[str, Any]],
    ) -> "GeneRegistry":
        self._entries.append((spec, fn))
        return self

    def run(
        self,
        context: GeneContext,
        progress: Callable[[int, str], None] | None = None,
    ) -> dict[str, Any]:
        entries = sorted(self._entries, key=lambda item: item[0].order)
        records: list[dict[str, Any]] = []
        total = max(1, len(entries))

        for index, (spec, fn) in enumerate(entries):
            if progress:
                percent = 8 + int((index / total) * 84)
                progress(percent, f"PROFILE: {spec.display_name}")
            records.append(run_gene(spec, context, fn))

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
            labels.append(
                {
                    "gene": record["id"],
                    "label": normalized.get("label"),
                    "confidence": normalized.get("confidence"),
                }
            )

    tonal: dict[str, Any] = {}
    if labels:
        counts: dict[str, int] = defaultdict(int)
        for item in labels:
            counts[str(item["label"])] += 1
        winner = max(counts.items(), key=lambda pair: pair[1])
        tonal = {
            "method": "label-vote-preserving-individual-confidence",
            "label": winner[0],
            "support": winner[1],
            "sources": labels,
            "unanimous": winner[1] == len(labels),
        }

    embedding_records = [
        record
        for record in records
        if record.get("family") == "embedding"
        and record.get("status") == "ok"
    ]

    return {
        "semantic": semantic,
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
        },
    }
