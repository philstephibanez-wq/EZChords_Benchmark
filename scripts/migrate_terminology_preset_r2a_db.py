from __future__ import annotations

import argparse
import sqlite3
import shutil
from datetime import datetime, timezone
from pathlib import Path


MIGRATION_ID = "20261010_preset_terminology_r2a"


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    if not table_exists(conn, table):
        return False
    return any(
        str(row[1]) == column
        for row in conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    )


def rename_table(conn: sqlite3.Connection, old: str, new: str) -> None:
    old_exists = table_exists(conn, old)
    new_exists = table_exists(conn, new)
    if old_exists and new_exists:
        raise RuntimeError(f"both_tables_exist:{old}:{new}")
    if old_exists:
        conn.execute(f'ALTER TABLE "{old}" RENAME TO "{new}"')


def rename_column(conn: sqlite3.Connection, table: str, old: str, new: str) -> None:
    if not table_exists(conn, table):
        return
    old_exists = column_exists(conn, table, old)
    new_exists = column_exists(conn, table, new)
    if old_exists and new_exists:
        raise RuntimeError(f"both_columns_exist:{table}:{old}:{new}")
    if old_exists:
        conn.execute(
            f'ALTER TABLE "{table}" RENAME COLUMN "{old}" TO "{new}"'
        )


def count_rows(conn: sqlite3.Connection, table: str) -> int:
    if not table_exists(conn, table):
        return 0
    return int(conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])


def rebuild_profile_validation(conn: sqlite3.Connection) -> None:
    table = "profile_human_validations"
    if not table_exists(conn, table):
        return

    cols = {str(r[1]) for r in conn.execute(f'PRAGMA table_info("{table}")')}
    if {
        "module_key",
        "phase_revision_ref",
        "module_revision_ref",
    }.issubset(cols):
        # Already canonical; only normalize scope/subject keys.
        conn.execute(
            "UPDATE profile_human_validations "
            "SET scope=CASE scope WHEN 'region' THEN 'phase' "
            "WHEN 'gene' THEN 'module' ELSE scope END"
        )
        conn.execute(
            "UPDATE profile_human_validations "
            "SET subject_key='phase:' || substr(subject_key,8) "
            "WHERE subject_key LIKE 'region:%'"
        )
        return

    conn.execute("DROP TABLE IF EXISTS profile_human_validations_r2a_new")
    conn.execute(
        """
CREATE TABLE profile_human_validations_r2a_new (
    run_id INTEGER NOT NULL,
    subject_key TEXT NOT NULL,
    scope TEXT NOT NULL CHECK(scope IN ('phase','module')),
    item_key TEXT NOT NULL,
    module_key TEXT,
    predicted_json TEXT NOT NULL DEFAULT '{}',
    verdict TEXT NOT NULL CHECK(verdict IN ('ok','ko','unknown')),
    human_value TEXT NOT NULL DEFAULT '',
    comment TEXT NOT NULL DEFAULT '',
    phase_revision_ref TEXT,
    module_revision_ref TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    missing_expected_json TEXT NOT NULL DEFAULT '[]',
    reviewer_certainty TEXT NOT NULL DEFAULT '',
    validation_schema TEXT NOT NULL DEFAULT 'ezstudio.profile-human.v2',
    PRIMARY KEY(run_id, subject_key),
    FOREIGN KEY(run_id) REFERENCES scientific_runs(id) ON DELETE CASCADE
)
"""
    )

    def src(name: str, fallback: str = "NULL") -> str:
        return f'"{name}"' if name in cols else fallback

    conn.execute(
        f"""
INSERT INTO profile_human_validations_r2a_new(
    run_id,subject_key,scope,item_key,module_key,
    predicted_json,verdict,human_value,comment,
    phase_revision_ref,module_revision_ref,
    created_at,updated_at,missing_expected_json,
    reviewer_certainty,validation_schema
)
SELECT
    run_id,
    CASE
      WHEN subject_key LIKE 'region:%'
      THEN 'phase:' || substr(subject_key,8)
      ELSE subject_key
    END,
    CASE scope
      WHEN 'region' THEN 'phase'
      WHEN 'gene' THEN 'module'
      ELSE scope
    END,
    item_key,
    {src("gene_key")},
    predicted_json,
    verdict,
    human_value,
    comment,
    {src("region_revision_ref")},
    {src("gene_revision_ref")},
    created_at,
    updated_at,
    {src("missing_expected_json", "'[]'")},
    {src("reviewer_certainty", "''")},
    {src("validation_schema", "'ezstudio.profile-human.v2'")}
FROM profile_human_validations
"""
    )
    conn.execute("DROP TABLE profile_human_validations")
    conn.execute(
        "ALTER TABLE profile_human_validations_r2a_new "
        "RENAME TO profile_human_validations"
    )

    conn.execute(
        "CREATE INDEX idx_profile_human_validation_subject "
        "ON profile_human_validations(subject_key, verdict)"
    )
    conn.execute(
        "CREATE INDEX idx_profile_human_validation_phase_revision "
        "ON profile_human_validations(phase_revision_ref, verdict)"
    )
    conn.execute(
        "CREATE INDEX idx_profile_human_validation_module_revision "
        "ON profile_human_validations(module_revision_ref, verdict)"
    )
    conn.execute(
        "CREATE INDEX idx_profile_human_validation_certainty "
        "ON profile_human_validations(reviewer_certainty, verdict)"
    )


def migrate(db: Path) -> Path:
    if not db.is_file():
        raise RuntimeError(f"database_missing:{db}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup = db.with_name(f"{db.name}.pre-{MIGRATION_ID}-{stamp}.bak")

    source = sqlite3.connect(db)
    source.execute("PRAGMA busy_timeout=5000")
    active = 0
    if table_exists(source, "analysis_jobs"):
        active = int(
            source.execute(
                "SELECT COUNT(*) FROM analysis_jobs "
                "WHERE status IN ('queued','running','cancelling')"
            ).fetchone()[0]
        )
    if active:
        source.close()
        raise RuntimeError(f"active_analysis_jobs:{active}")

    # SQLite online-consistent backup.
    dest = sqlite3.connect(backup)
    source.backup(dest)
    dest.close()
    source.close()

    conn = sqlite3.connect(db)
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=OFF")
    conn.execute("PRAGMA legacy_alter_table=OFF")

    before = {
        "module_revisions": count_rows(
            conn,
            "genome_gene_revisions"
            if table_exists(conn, "genome_gene_revisions")
            else "preset_module_revisions",
        ),
        "phase_revisions": count_rows(
            conn,
            "genome_region_revisions"
            if table_exists(conn, "genome_region_revisions")
            else "preset_phase_revisions",
        ),
        "run_preset_links": count_rows(
            conn,
            "scientific_run_genome"
            if table_exists(conn, "scientific_run_genome")
            else "scientific_run_preset",
        ),
        "human_validations": count_rows(conn, "profile_human_validations"),
    }

    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute(
            """
CREATE TABLE IF NOT EXISTS ezstudio_schema_migrations (
    migration_id TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
)
"""
        )
        applied = conn.execute(
            "SELECT 1 FROM ezstudio_schema_migrations WHERE migration_id=?",
            (MIGRATION_ID,),
        ).fetchone()

        if not applied:
            # Core preset history.
            rename_table(conn, "genome_gene_revisions", "preset_module_revisions")
            rename_table(conn, "genome_region_revisions", "preset_phase_revisions")
            rename_table(
                conn,
                "genome_region_revision_genes",
                "preset_phase_revision_modules",
            )
            rename_table(
                conn,
                "genome_region_revision_parents",
                "preset_phase_revision_parents",
            )
            rename_table(conn, "scientific_run_genome", "scientific_run_preset")
            rename_table(
                conn,
                "genome_region_baselines",
                "preset_phase_baselines",
            )

            rename_column(
                conn, "preset_module_revisions", "gene_key", "module_key"
            )
            rename_column(conn, "preset_phase_revisions", "region", "phase")
            rename_column(
                conn,
                "preset_phase_revision_modules",
                "region_revision_id",
                "phase_revision_id",
            )
            rename_column(
                conn,
                "preset_phase_revision_modules",
                "gene_revision_id",
                "module_revision_id",
            )
            rename_column(
                conn,
                "preset_phase_revision_parents",
                "child_region_revision_id",
                "child_phase_revision_id",
            )
            rename_column(
                conn,
                "preset_phase_revision_parents",
                "parent_region_revision_id",
                "parent_phase_revision_id",
            )
            rename_column(
                conn,
                "scientific_run_preset",
                "region_revision_id",
                "phase_revision_id",
            )
            rename_column(
                conn,
                "preset_phase_baselines",
                "region",
                "phase",
            )
            rename_column(
                conn,
                "preset_phase_baselines",
                "region_revision_id",
                "phase_revision_id",
            )

            # Canonical index names.
            conn.execute("DROP INDEX IF EXISTS idx_genome_gene_key")
            conn.execute("DROP INDEX IF EXISTS idx_genome_region_revision")
            if table_exists(conn, "preset_module_revisions"):
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_preset_module_key "
                    "ON preset_module_revisions(module_key, revision_number)"
                )
            if table_exists(conn, "preset_phase_revisions"):
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_preset_phase_revision "
                    "ON preset_phase_revisions(phase, revision_number)"
                )

            rebuild_profile_validation(conn)

            # Resource-lock vocabulary.
            if table_exists(conn, "analysis_resource_locks"):
                rename_column(
                    conn,
                    "analysis_resource_locks",
                    "region",
                    "phase",
                )
            conn.execute("DROP TRIGGER IF EXISTS trg_analysis_jobs_region_lock_insert")
            conn.execute("DROP TRIGGER IF EXISTS trg_analysis_jobs_region_lock_claim")

            # Canonical scientific labels, conflict-safe if a new label
            # already exists for the same run.
            if table_exists(conn, "scientific_run_labels"):
                for old_label, new_label in (
                    ("genome_region_revision", "preset_phase_revision"),
                    ("genome_region_fingerprint", "preset_phase_fingerprint"),
                    ("abandoned_from_region", "abandoned_from_phase"),
                ):
                    conn.execute(
                        "INSERT INTO scientific_run_labels(run_id,label,value) "
                        "SELECT run_id,?,value FROM scientific_run_labels "
                        "WHERE label=? "
                        "ON CONFLICT(run_id,label) DO UPDATE SET value=excluded.value",
                        (new_label, old_label),
                    )
                    conn.execute(
                        "DELETE FROM scientific_run_labels WHERE label=?",
                        (old_label,),
                    )

            conn.execute(
                "INSERT INTO ezstudio_schema_migrations(migration_id,applied_at) "
                "VALUES(?,?)",
                (MIGRATION_ID, datetime.now(timezone.utc).isoformat()),
            )

        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        raise

    conn.execute("PRAGMA foreign_keys=ON")

    after = {
        "module_revisions": count_rows(conn, "preset_module_revisions"),
        "phase_revisions": count_rows(conn, "preset_phase_revisions"),
        "run_preset_links": count_rows(conn, "scientific_run_preset"),
        "human_validations": count_rows(conn, "profile_human_validations"),
    }
    if before != after:
        conn.close()
        raise RuntimeError(f"row_count_mismatch:before={before}:after={after}")

    fk = conn.execute("PRAGMA foreign_key_check").fetchall()
    if fk:
        conn.close()
        raise RuntimeError(f"foreign_key_check_failed:{fk[:5]}")

    integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
    if integrity.lower() != "ok":
        conn.close()
        raise RuntimeError(f"integrity_check_failed:{integrity}")

    conn.close()

    print("TERMINOLOGY_PRESET_R2A_DB_MIGRATION_OK")
    print(f"backup={backup}")
    print(f"counts={after}")
    return backup


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db",
        default=str(
            Path(__file__).resolve().parents[1] / "data" / "benchmark.sqlite"
        ),
    )
    args = parser.parse_args()
    migrate(Path(args.db).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
