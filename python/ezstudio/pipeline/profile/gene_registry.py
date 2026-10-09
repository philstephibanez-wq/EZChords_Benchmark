from __future__ import annotations

from collections import defaultdict
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


def build_consensus(records: list[dict[str, Any]]) -> dict[str, Any]:
    semantic_records = [
        record
        for record in records
        if record.get("family") == "semantic"
        and record.get("status") == "ok"
    ]

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
            semantic[family] = {
                "method": (
                    "exact-label-agreement-"
                    "no-cross-engine-score-calibration"
                ),
                "agreements": agreements,
                "divergences": divergences,
                "per_engine": per_engine,
            }

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
        },
    }
