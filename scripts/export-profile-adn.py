from __future__ import annotations

import argparse
import json
import sqlite3
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _json_default(value: Any):
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    return str(value)


def _safe(value: str) -> str:
    import re
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    return text.strip("-._") or "item"


def _rows(conn: sqlite3.Connection, sql: str, params=()) -> list[dict]:
    cur = conn.execute(sql, params)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def _tables(conn: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }


def _decode_json_fields(row: dict) -> dict:
    out = dict(row)
    for key, value in list(out.items()):
        if key.endswith("_json") and isinstance(value, str):
            try:
                out[key[:-5]] = json.loads(value)
            except Exception:
                pass
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--song-id", required=True, type=int)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    db_path = Path(args.db)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    tables = _tables(conn)

    songs = _rows(conn, "SELECT * FROM songs WHERE id=?", (args.song_id,))
    if not songs:
        raise RuntimeError("catalog_song_not_found")
    song = songs[0]
    audio_sha256 = str(song.get("audio_sha256") or "")

    song_ids = [args.song_id]
    if audio_sha256:
        song_ids = [
            int(row["id"])
            for row in _rows(
                conn,
                "SELECT id FROM songs WHERE audio_sha256=? ORDER BY id",
                (audio_sha256,),
            )
        ]

    marks = ",".join("?" for _ in song_ids)

    scientific_runs: list[dict] = []
    if "scientific_runs" in tables:
        scientific_runs = [
            _decode_json_fields(row)
            for row in _rows(
                conn,
                f"""SELECT * FROM scientific_runs
                    WHERE song_id IN ({marks})
                      AND item='profile'
                    ORDER BY id DESC""",
                tuple(song_ids),
            )
        ]

    analysis_jobs: list[dict] = []
    if "analysis_jobs" in tables:
        analysis_jobs = [
            _decode_json_fields(row)
            for row in _rows(
                conn,
                f"""SELECT * FROM analysis_jobs
                    WHERE song_id IN ({marks})
                      AND kind='profile'
                    ORDER BY id DESC""",
                tuple(song_ids),
            )
        ]

    artifacts_by_run: dict[int, list[dict]] = {}
    if "scientific_artifacts" in tables and scientific_runs:
        run_ids = [int(r["id"]) for r in scientific_runs]
        run_marks = ",".join("?" for _ in run_ids)
        for row in _rows(
            conn,
            f"""SELECT * FROM scientific_artifacts
                WHERE run_id IN ({run_marks})
                ORDER BY run_id,id""",
            tuple(run_ids),
        ):
            artifacts_by_run.setdefault(int(row["run_id"]), []).append(
                _decode_json_fields(row)
            )

    manifest = {
        "schema": "ezstudio.profile.feedback.v2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "audio_included": False,
        "song": song,
        "catalog_song_ids": song_ids,
        "counts": {
            "scientific_runs": len(scientific_runs),
            "analysis_jobs": len(analysis_jobs),
        },
    }

    with zipfile.ZipFile(
        output,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as z:
        z.writestr(
            "manifest.json",
            json.dumps(manifest, ensure_ascii=False, indent=2, default=_json_default) + "\n",
        )
        z.writestr(
            "sqlite/analysis_jobs.json",
            json.dumps(analysis_jobs, ensure_ascii=False, indent=2, default=_json_default) + "\n",
        )

        for run in scientific_runs:
            run_id = int(run["id"])
            public_id = str(run.get("public_id") or f"profile-{run_id}")
            payload = dict(run)
            payload["artifacts"] = artifacts_by_run.get(run_id, [])
            z.writestr(
                f"sqlite/runs/{_safe(public_id)}.json",
                json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default) + "\n",
            )

            for artifact in artifacts_by_run.get(run_id, []):
                path = Path(str(artifact.get("path") or ""))
                if path.is_file() and path.suffix.lower() == ".json":
                    z.write(
                        path,
                        f"artifacts/{_safe(public_id)}/{_safe(path.name)}",
                    )

        z.writestr(
            "README.txt",
            "EZStudio_lab PROFILE ADN feedback bundle v2\n"
            "Sources: SQLite + JSON artifacts.\n"
            "No source audio or stems included.\n",
        )

    print(f"EZSTUDIO_PROFILE_ADN_EXPORT_OK {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
