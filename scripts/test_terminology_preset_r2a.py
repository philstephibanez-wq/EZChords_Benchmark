from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "benchmark.sqlite"

assert DB.is_file(), DB
conn = sqlite3.connect(DB)
tables = {
    str(r[0])
    for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
}

required = {
    "preset_module_revisions",
    "preset_phase_revisions",
    "preset_phase_revision_modules",
    "preset_phase_revision_parents",
    "scientific_run_preset",
    "preset_phase_baselines",
}
missing = sorted(required - tables)
assert not missing, missing

forbidden = {
    "genome_gene_revisions",
    "genome_region_revisions",
    "genome_region_revision_genes",
    "genome_region_revision_parents",
    "scientific_run_genome",
    "genome_region_baselines",
}
present = sorted(forbidden & tables)
assert not present, present

def cols(table: str) -> set[str]:
    return {str(r[1]) for r in conn.execute(f'PRAGMA table_info("{table}")')}

assert "module_key" in cols("preset_module_revisions")
assert "phase" in cols("preset_phase_revisions")
assert {"phase_revision_id","module_revision_id"} <= cols("preset_phase_revision_modules")
assert "phase_revision_id" in cols("scientific_run_preset")
assert {"phase","phase_revision_id"} <= cols("preset_phase_baselines")

if "profile_human_validations" in tables:
    c = cols("profile_human_validations")
    assert "module_key" in c
    assert "phase_revision_ref" in c
    assert "module_revision_ref" in c
    bad_scope = conn.execute(
        "SELECT COUNT(*) FROM profile_human_validations "
        "WHERE scope IN ('region','gene')"
    ).fetchone()[0]
    assert int(bad_scope) == 0

if "analysis_resource_locks" in tables:
    c = cols("analysis_resource_locks")
    assert "phase" in c
    assert "region" not in c

assert not conn.execute("PRAGMA foreign_key_check").fetchall()
assert str(conn.execute("PRAGMA integrity_check").fetchone()[0]).lower() == "ok"
conn.close()

preset = (ROOT / "src/Service/PresetRegistry.php").read_text(encoding="utf-8")
assert "preset_module_revisions" in preset
assert "preset_phase_revisions" in preset
assert "captureRunPreset" in preset

profile_validation = (
    ROOT / "src/Service/ProfileValidationService.php"
).read_text(encoding="utf-8")
assert "scientific_run_preset" in profile_validation
assert "preset_phase_revisions" in profile_validation
assert "module_revision_ref" in profile_validation

home = (ROOT / "templates/workbench/home.html.twig").read_text(encoding="utf-8")
assert "Chaîne d’analyse" in home
assert "Chromosome analytique" not in home
assert "preset_export_zip" in home

assert (ROOT / "scripts/export-presets.py").is_file()
assert not (ROOT / "scripts/export-chromosome-adn.py").exists()
assert (ROOT / "src/Controller/PresetExportController.php").is_file()
assert not (ROOT / "src/Controller/ChromosomeAdnController.php").exists()

print("TERMINOLOGY_PRESET_R2A_CONTRACT_OK")
print("SQLite schema aligned with Preset / Phase / Module terminology")
print("No scientific algorithm change asserted by this contract")
