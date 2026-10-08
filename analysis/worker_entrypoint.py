from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

PROTOCOL = "ezscore.analysis-job.v2"
ALLOWED_KINDS = {"benchmark", "profile", "stems", "chords_scientific"}


def _resolved(path: Path) -> Path:
    return path.resolve(strict=False)


def _is_under(path: Path, root: Path) -> bool:
    try:
        _resolved(path).relative_to(_resolved(root))
        return True
    except ValueError:
        return False


def _required_string(mapping: dict[str, Any], key: str) -> str:
    value = str(mapping.get(key) or "").strip()
    if not value:
        raise RuntimeError(f"missing_{key}")
    return value


def _common_env(runtime_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("EZSTUDIO_RUNTIME_ROOT", str(runtime_root))
    env.setdefault("BS_ROFORMER_MODELS_PATH", r"H:\EZScoreModels\bs-roformer")
    env.setdefault("MELBAND_ROFORMER_MODELS_PATH", r"H:\EZScoreModels\melband-roformer")
    env.setdefault("EZSTUDIO_STEM_DEVICE", "cuda:0")
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-file", required=True)
    args = parser.parse_args()

    job_file = Path(args.job_file).resolve()
    raw = json.loads(job_file.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise RuntimeError("job_envelope_must_be_object")

    if str(raw.get("protocol") or "") != PROTOCOL:
        raise RuntimeError("unsupported_job_protocol")
    if str(raw.get("target") or "").strip().lower() != "lab":
        raise RuntimeError("job_target_must_be_lab")
    if str(os.getenv("EZS_TARGET", "") or "").strip().lower() != "lab":
        raise RuntimeError("EZS_TARGET_must_be_lab")

    kind = str(raw.get("kind") or "").strip().lower()
    if kind not in ALLOWED_KINDS:
        raise RuntimeError(f"unsupported_job_kind:{raw.get('kind')}")

    project_root = Path(__file__).resolve().parents[1]
    expected_root_raw = str(os.getenv("EZS_EXPECTED_ROOT", "") or "").strip()
    if not expected_root_raw:
        raise RuntimeError("EZS_EXPECTED_ROOT_missing")
    expected_root = Path(expected_root_raw)
    if _resolved(expected_root) != _resolved(project_root):
        raise RuntimeError(
            f"unexpected_project_root:expected={expected_root};actual={project_root}"
        )

    paths = raw.get("paths") if isinstance(raw.get("paths"), dict) else {}
    request = raw.get("request") if isinstance(raw.get("request"), dict) else {}

    source = Path(_required_string(paths, "source"))
    progress_file = Path(_required_string(paths, "progress_file"))
    if not source.is_file():
        raise RuntimeError(f"source_missing:{source}")

    runtime_root = Path(
        str(os.getenv("EZSTUDIO_RUNTIME_ROOT", r"H:\temp\EZStudio_lab"))
    )
    if not _is_under(source, project_root):
        raise RuntimeError(f"source_outside_lab_root:{source}")
    if not _is_under(progress_file, runtime_root):
        raise RuntimeError(f"progress_outside_lab_runtime:{progress_file}")

    env = _common_env(runtime_root)

    if kind == "profile":
        runner = project_root / "python" / "ezstudio" / "pipeline" / "profile" / "runner.py"
        if not runner.is_file():
            raise RuntimeError(f"profile_runner_missing:{runner}")
        audio_hash = _required_string(request, "audio_hash")
        output_path = Path(_required_string(request, "output_path"))
        if not _is_under(output_path, runtime_root):
            raise RuntimeError(f"profile_output_outside_lab_runtime:{output_path}")
        command = [
            sys.executable, str(runner),
            "--source", str(source),
            "--audio-hash", audio_hash,
            "--output-path", str(output_path),
            "--progress-file", str(progress_file),
        ]
        completed = subprocess.run(command, cwd=str(project_root), env=env, check=False)
        return int(completed.returncode)

    if kind == "stems":
        runner = project_root / "python" / "ezstudio" / "pipeline" / "stems" / "runner.py"
        if not runner.is_file():
            raise RuntimeError(f"stems_runner_missing:{runner}")

        audio_hash = _required_string(request, "audio_hash")
        storage_root = Path(_required_string(request, "storage_root"))
        if not _is_under(storage_root, runtime_root):
            raise RuntimeError(f"stems_storage_outside_lab_runtime:{storage_root}")

        command = [
            sys.executable,
            str(runner),
            "--source", str(source),
            "--audio-hash", audio_hash,
            "--storage-root", str(storage_root),
            "--progress-file", str(progress_file),
        ]
        if bool(request.get("force", False)):
            command.append("--force")

        completed = subprocess.run(
            command,
            cwd=str(project_root),
            env=env,
            check=False,
        )
        return int(completed.returncode)

    database = Path(_required_string(request, "database"))
    deps = Path(_required_string(request, "deps"))
    run_id = int(request.get("run_id") or 0)
    signature = _required_string(request, "signature")
    keep_upload = "1" if bool(request.get("keep_upload", True)) else "0"
    selection_request_raw = str(request.get("selection_request") or "").strip()
    selection_request = Path(selection_request_raw) if selection_request_raw else None

    if run_id <= 0:
        raise RuntimeError("invalid_run_id")
    if not _is_under(database, project_root):
        raise RuntimeError(f"database_outside_lab_root:{database}")
    if not _is_under(deps, runtime_root):
        raise RuntimeError(f"deps_outside_lab_runtime:{deps}")
    if kind == "chords_scientific":
        if selection_request is None or not selection_request.is_file():
            raise RuntimeError("selection_request_missing")
        if not _is_under(selection_request, runtime_root):
            raise RuntimeError(
                f"selection_request_outside_lab_runtime:{selection_request}"
            )

    worker = project_root / "python" / "worker.py"
    if not worker.is_file():
        raise RuntimeError(f"benchmark_worker_missing:{worker}")

    progress_file.parent.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        str(worker),
        "--db", str(database),
        "--run-id", str(run_id),
        "--audio", str(source),
        "--signature", signature,
        "--deps", str(deps),
        "--keep-upload", keep_upload,
        "--progress-file", str(progress_file),
    ]
    if kind == "chords_scientific":
        command += ["--selection-request", str(selection_request)]

    env.setdefault("EZSTUDIO_DEP_ROOT", str(deps))
    env.setdefault("EZSTUDIO_STEMS_CACHE_ROOT", str(runtime_root / "stems"))
    env.setdefault("EZSTUDIO_OBSERVABILITY_ROOT", str(runtime_root / "observability"))
    env.setdefault("EZSTUDIO_EXPORT_ROOT", str(runtime_root / "exports"))

    completed = subprocess.run(
        command,
        cwd=str(project_root),
        env=env,
        check=False,
    )
    return int(completed.returncode)


if __name__ == "__main__":
    # R3B10D_MONGO_TERMINAL_EVENT
    from mongo_science import record_terminal_event

    try:
        _rc = int(main())
    except BaseException as _exc:
        record_terminal_event(
            returncode=1,
            error=f"{type(_exc).__name__}:{_exc}",
        )
        raise
    else:
        record_terminal_event(
            returncode=_rc,
            error=None if _rc == 0 else f"analysis_returncode={_rc}",
        )
        raise SystemExit(_rc)
