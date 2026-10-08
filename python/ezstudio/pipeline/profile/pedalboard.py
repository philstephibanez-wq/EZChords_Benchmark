from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

from pedal import PedalContext, PedalSpec, run_pedal


class Pedalboard:
    def __init__(self) -> None:
        self._entries: list[tuple[PedalSpec, Callable[[PedalContext], dict[str, Any]]]] = []

    def add(
        self,
        spec: PedalSpec,
        fn: Callable[[PedalContext], dict[str, Any]],
    ) -> "Pedalboard":
        self._entries.append((spec, fn))
        return self

    def run(
        self,
        context: PedalContext,
        progress: Callable[[int, str], None] | None = None,
    ) -> dict[str, Any]:
        entries = sorted(self._entries, key=lambda item: item[0].order)
        records: list[dict[str, Any]] = []
        total = max(1, len(entries))

        for index, (spec, fn) in enumerate(entries):
            if progress:
                percent = 10 + int((index / total) * 80)
                progress(percent, f"PROFILE: {spec.display_name}")
            records.append(run_pedal(spec, context, fn))

        by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            by_family[str(record.get("family") or "unknown")].append(record)

        return {
            "schema": "ezstudio.profile.pedalboard.v1",
            "pedals": records,
            "families": dict(by_family),
            "consensus": build_consensus(records),
        }


def _semantic_rows(record: dict[str, Any], family: str) -> list[dict[str, Any]]:
    normalized = record.get("normalized")
    if not isinstance(normalized, dict):
        return []
    rows = normalized.get(family)
    return rows if isinstance(rows, list) else []


def build_consensus(records: list[dict[str, Any]]) -> dict[str, Any]:
    semantic_records = [
        record for record in records
        if record.get("family") == "semantic" and record.get("status") == "ok"
    ]

    semantic: dict[str, Any] = {}
    for family in ("genre", "instrumentation", "mood", "voice"):
        support: dict[str, list[dict[str, Any]]] = defaultdict(list)
        per_engine: dict[str, list[dict[str, Any]]] = {}

        for record in semantic_records:
            rows = _semantic_rows(record, family)
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
                        "pedal": record["id"],
                    }
                )

        agreements = []
        divergences = []
        for items in support.values():
            canonical = items[0]["label"]
            row = {
                "label": canonical,
                "support": len(items),
                "pedals": [item["pedal"] for item in items],
                "mean_source_score": round(
                    sum(item["score"] for item in items) / len(items), 4
                ),
            }
            if len(items) >= 2:
                agreements.append(row)
            else:
                divergences.append(row)

        agreements.sort(
            key=lambda row: (row["support"], row["mean_source_score"]),
            reverse=True,
        )
        divergences.sort(
            key=lambda row: row["mean_source_score"],
            reverse=True,
        )

        semantic[family] = {
            "method": "exact-label-agreement-no-cross-engine-score-calibration",
            "agreements": agreements,
            "divergences": divergences,
            "per_engine": per_engine,
        }

    tonal = {}
    tonal_records = [
        record for record in records
        if record.get("family") == "tonal" and record.get("status") == "ok"
    ]
    labels = []
    for record in tonal_records:
        normalized = record.get("normalized")
        if isinstance(normalized, dict) and normalized.get("label"):
            labels.append(
                {
                    "pedal": record["id"],
                    "label": normalized.get("label"),
                    "confidence": normalized.get("confidence"),
                }
            )
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
        }

    return {
        "semantic": semantic,
        "tonal": tonal,
        "policy": {
            "cross_engine_scores_are_not_assumed_calibrated": True,
            "raw_and_normalized_outputs_are_preserved": True,
            "divergence_is_preserved": True,
        },
    }
