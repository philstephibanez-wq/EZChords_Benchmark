from __future__ import annotations

import gc
import hashlib
import platform
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np

from perf_probe import GenePerformanceProbe


@dataclass(frozen=True)
class ModuleConfig:
    module_id: str
    display_name: str
    family: str
    order: int
    engine: str
    engine_version: str | None = None
    model_id: str | None = None
    model_path: str | None = None
    device: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    thresholds: dict[str, Any] = field(default_factory=dict)
    weights: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModuleContext:
    source: Path
    audio_sha256: str
    y: np.ndarray
    sr: int
    model_root: Path
    ai_models_root: Path


def file_sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def release_accelerator_memory() -> None:
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


def run_module(
    config: ModuleConfig,
    context: ModuleContext,
    fn: Callable[[GeneContext], dict[str, Any]],
) -> dict[str, Any]:
    started = time.perf_counter()
    record: dict[str, Any] = {
        "id": config.module_id,
        "name": config.display_name,
        "family": config.family,
        "order": config.order,
        "status": "running",
        "engine": {
            "name": config.engine,
            "version": config.engine_version,
        },
        "model": {
            "id": config.model_id,
            "path": config.model_path,
        },
        "device": config.device,
        "parameters": config.parameters,
        "thresholds": config.thresholds,
        "weights": config.weights,
        "input": {
            "audio_sha256": context.audio_sha256,
            "sample_rate": context.sr,
            "samples": int(context.y.size),
        },
        "raw": None,
        "normalized": None,
        "calibrated": {
            "status": "not_calibrated",
            "method": None,
            "confidence": None,
        },
        "warnings": [],
        "error": None,
    }

    perf_probe = GenePerformanceProbe(
        gene_id=config.module_id,
        gene_name=config.display_name,
        family=config.family,
        device=config.device,
        audio_sha256=context.audio_sha256,
    )
    perf_probe.start()

    try:
        output = fn(context) or {}
        record["raw"] = output.get("raw")
        record["normalized"] = output.get("normalized", output.get("raw"))
        if isinstance(output.get("calibrated"), dict):
            record["calibrated"] = output["calibrated"]
        record["warnings"] = list(output.get("warnings") or [])
        if isinstance(output.get("engine"), dict):
            record["engine"].update(output["engine"])
        if isinstance(output.get("model"), dict):
            record["model"].update(output["model"])
        if output.get("device"):
            record["device"] = output["device"]
        requested_status = str(output.get("status") or "ok")
        record["status"] = requested_status if requested_status in {"ok", "skipped"} else "ok"
    except Exception as exc:
        record["status"] = "error"
        record["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
    finally:
        elapsed = round(time.perf_counter() - started, 4)
        record["timing"] = {
            "elapsed_seconds": elapsed,
        }
        try:
            perf_probe.finish(
                status=str(record.get("status") or "error"),
                elapsed_seconds=elapsed,
            )
        except Exception:
            pass
        release_accelerator_memory()

    return record


# Legacy aliases retained for terminology-migration compatibility.
GeneSpec = ModuleConfig
GeneContext = ModuleContext
run_gene = run_module
