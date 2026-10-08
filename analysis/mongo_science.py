from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _dep_root() -> Path:
    return Path(os.getenv("EZSTUDIO_MONGO_DEP_ROOT", r"H:\temp\EZStudio_lab\deps\mongo-r1"))


def _prepare_imports() -> None:
    root = _dep_root()
    if root.is_dir() and str(root) not in sys.path:
        sys.path.append(str(root))


def _mongo():
    _prepare_imports()
    from pymongo import MongoClient

    uri = os.getenv("EZSTUDIO_MONGO_URI", "mongodb://127.0.0.1:27017")
    db_name = os.getenv("EZSTUDIO_MONGO_DB", "ezstudio_lab")
    client = MongoClient(uri, serverSelectionTimeoutMS=2500)
    client.admin.command("ping")
    return client, client[db_name]


def _job_file_from_argv() -> Path | None:
    try:
        idx = sys.argv.index("--job-file")
    except ValueError:
        return None
    if idx + 1 >= len(sys.argv):
        return None
    return Path(sys.argv[idx + 1]).resolve(strict=False)


def record_terminal_event(*, returncode: int, error: str | None = None) -> None:
    try:
        job_file = _job_file_from_argv()
        raw: dict[str, Any] = {}
        if job_file is not None and job_file.is_file():
            loaded = json.loads(job_file.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                raw = loaded

        request = raw.get("request") if isinstance(raw.get("request"), dict) else {}
        song = raw.get("song") if isinstance(raw.get("song"), dict) else {}

        event = {
            "schema": "ezstudio.science.event.v1",
            "event_type": "analysis_job_terminal",
            "target": str(raw.get("target") or "lab").lower(),
            "job_id": int(raw.get("job_id") or 0) or None,
            "kind": str(raw.get("kind") or ""),
            "song_id": int(raw.get("song_id") or 0) or None,
            "song_title": str(song.get("title") or ""),
            "song_artist": str(song.get("artist") or ""),
            "run_id": int(request.get("run_id") or 0) or None,
            "scientific_run_id": int(request.get("scientific_run_id") or 0) or None,
            "audio_sha256": str(request.get("audio_sha256") or request.get("audio_hash") or ""),
            "returncode": int(returncode),
            "status": "completed" if int(returncode) == 0 else "failed",
            "error": str(error or "")[:4000] or None,
            "occurred_at": datetime.now(timezone.utc),
        }

        client, db = _mongo()
        try:
            db.events.insert_one(event)
            db.events.create_index([("job_id", 1), ("occurred_at", -1)])
            db.events.create_index([("song_id", 1), ("kind", 1), ("occurred_at", -1)])
        finally:
            client.close()

        print(json.dumps({
            "event": "mongo_science_event",
            "job_id": event["job_id"],
            "kind": event["kind"],
            "status": event["status"],
        }, ensure_ascii=False), flush=True)
    except Exception as exc:
        print(
            f"MONGO_SCIENCE_EVENT_ERROR:{type(exc).__name__}:{exc}",
            file=sys.stderr,
            flush=True,
        )
