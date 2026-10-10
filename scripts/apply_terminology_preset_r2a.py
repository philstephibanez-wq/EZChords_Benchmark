from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    p = ROOT / rel
    if not p.is_file():
        raise RuntimeError(f"required_file_missing:{rel}")
    return p.read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")


def remove_accidental_grep_artifact() -> int:
    removed = 0
    for p in ROOT.iterdir():
        if not p.is_file():
            continue
        try:
            raw = p.read_bytes()
        except OSError:
            continue
        if (
            raw.startswith(b"\x1b[35mpython/engine.py")
            and b"gene_registry.py" in raw
            and b"ChromosomeAdnController.php" in raw
        ):
            p.unlink()
            removed += 1
    return removed


def canonicalize_analysis_registry() -> None:
    legacy = read("src/Service/DnaRegistry.php")
    if "class DnaRegistry" not in legacy:
        raise RuntimeError("DnaRegistry_class_marker_missing")
    canonical = legacy.replace("class DnaRegistry", "class AnalysisRunRegistry", 1)
    write("src/Service/AnalysisRunRegistry.php", canonical)
    write(
        "src/Service/DnaRegistry.php",
        """<?php
namespace App\\Service;

/** @deprecated Compatibility alias; use AnalysisRunRegistry. */
class DnaRegistry extends AnalysisRunRegistry
{
}
""",
    )


def canonicalize_preset_registry() -> None:
    legacy = read("src/Service/GenomeRegistry.php")
    if "class GenomeRegistry" not in legacy:
        raise RuntimeError("GenomeRegistry_class_marker_missing")

    text = legacy.replace("class GenomeRegistry", "class PresetRegistry", 1)

    replacements = [
        ("genome_gene_revisions", "preset_module_revisions"),
        ("genome_region_revisions", "preset_phase_revisions"),
        ("genome_region_revision_genes", "preset_phase_revision_modules"),
        ("genome_region_revision_parents", "preset_phase_revision_parents"),
        ("scientific_run_genome", "scientific_run_preset"),
        ("genome_region_baselines", "preset_phase_baselines"),
        ("gene_revision_id", "module_revision_id"),
        ("region_revision_id", "phase_revision_id"),
        ("child_region_revision_id", "child_phase_revision_id"),
        ("parent_region_revision_id", "parent_phase_revision_id"),
        ("gene_key", "module_key"),
        ("idx_genome_gene_key", "idx_preset_module_key"),
        ("idx_genome_region_revision", "idx_preset_phase_revision"),
        ("captureRunGenome", "captureRunPreset"),
        ("genomeForRun", "presetForRun"),
        ("promoteRegionRevision", "promotePhaseRevision"),
        ("rejectRegionRevision", "rejectPhaseRevision"),
        ("diffRegionRevisions", "diffPhaseRevisions"),
        ("regionRevision", "phaseRevision"),
        ("genome_manifest", "preset_manifest"),
        ("genome_", "preset_"),
        ("geneRows", "moduleRows"),
        ("geneRow", "moduleRow"),
        ("geneKey", "moduleKey"),
        ("geneRevision", "moduleRevision"),
        ("regionFingerprint", "phaseFingerprint"),
        ("regionIdentity", "phaseIdentity"),
        ("regionRow", "phaseRow"),
        ("regionId", "phaseId"),
        ("regionRevision", "phaseRevision"),
        ("regions", "phases"),
        ("region", "phase"),
        ("genes", "modules"),
        ("gene", "module"),
        ("Genome", "Preset"),
        ("Gene", "Module"),
        ("Region", "Phase"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)

    text = text.replace(
        "$modules = $manifest['modules'] ?? null;",
        "$modules = $manifest['modules'] ?? $manifest['genes'] ?? null;",
    )
    text = text.replace(
        "'schema' => 'ezstudio.preset.phase.v1',",
        "'schema' => 'ezstudio.preset.phase.v1',",
    )
    # Canonical class must remain extensible for the compatibility alias.
    text = text.replace("final class PresetRegistry", "class PresetRegistry")
    write("src/Service/PresetRegistry.php", text)

    write(
        "src/Service/GenomeRegistry.php",
        """<?php
namespace App\\Service;

/** @deprecated Compatibility alias; use PresetRegistry. */
class GenomeRegistry extends PresetRegistry
{
    public function captureRunGenome(int $runId, string $region, array $manifest): array
    {
        return $this->captureRunPreset($runId, $region, $manifest);
    }

    public function genomeForRun(int $runId): ?array
    {
        return $this->presetForRun($runId);
    }

    public function regionRevision(int $id): array
    {
        return $this->phaseRevision($id);
    }

    public function promoteRegionRevision(int $id): array
    {
        return $this->promotePhaseRevision($id);
    }

    public function rejectRegionRevision(int $id): void
    {
        $this->rejectPhaseRevision($id);
    }

    public function diffRegionRevisions(int $fromId, int $toId): array
    {
        return $this->diffPhaseRevisions($fromId, $toId);
    }
}
""",
    )


def patch_profile_execution() -> None:
    p = ROOT / "src/Service/ProfileDnaExecutionService.php"
    if not p.is_file():
        return
    text = p.read_text(encoding="utf-8")
    text = text.replace("$genomeManifest", "$presetManifest")
    text = text.replace("$regionRevision", "$phaseRevision")
    text = text.replace(
        "$result['genome'] ?? null",
        "$result['preset'] ?? $result['genome'] ?? null",
    )
    text = text.replace(
        "profile_genome_manifest_missing",
        "profile_preset_manifest_missing",
    )
    text = text.replace("captureRunGenome", "captureRunPreset")
    text = text.replace(
        "'genome_region_revision'",
        "'preset_phase_revision'",
    )
    text = text.replace(
        "'genome_region_fingerprint'",
        "'preset_phase_fingerprint'",
    )
    text = text.replace(
        "'gene_registry' => $result['gene_registry'] ?? []",
        "'module_registry' => $result['module_registry'] ?? $result['gene_registry'] ?? []",
    )
    p.write_text(text, encoding="utf-8", newline="\n")


def patch_profile_validation() -> None:
    rel = "src/Service/ProfileValidationService.php"
    text = read(rel)

    replacements = [
        ("scope IN ('region','gene')", "scope IN ('phase','module')"),
        ("gene_key", "module_key"),
        ("region_revision_ref", "phase_revision_ref"),
        ("gene_revision_ref", "module_revision_ref"),
        ("idx_profile_human_validation_region_revision", "idx_profile_human_validation_phase_revision"),
        ("idx_profile_human_validation_gene_revision", "idx_profile_human_validation_module_revision"),
        ("$regionRevision", "$phaseRevision"),
        ("$geneRevisions", "$moduleRevisions"),
        ("$geneRevision", "$moduleRevision"),
        ("$geneKey", "$moduleKey"),
        ("'gene_key'", "'module_key'"),
        ("'region:'", "'phase:'"),
        ("'scope' => 'region'", "'scope' => 'phase'"),
        ("presetsRefs", "presetRefs"),
        ("genomeRefs", "presetRefs"),
        ("scientific_run_genome", "scientific_run_preset"),
        ("genome_region_revisions", "preset_phase_revisions"),
        ("genome_region_revision_genes", "preset_phase_revision_modules"),
        ("genome_gene_revisions", "preset_module_revisions"),
        ("region_revision_id", "phase_revision_id"),
        ("gene_revision_id", "module_revision_id"),
        ("gene_key", "module_key"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)

    # SQL aliases/local naming in the helper.
    text = re.sub(r"\$region\b", "$phase", text)
    text = re.sub(r"\$genes\b", "$modules", text)
    write(rel, text)


def patch_database_phase_lock_vocabulary() -> None:
    rel = "src/Service/Database.php"
    text = read(rel)

    # Only terminology around the resource-lock subsystem.
    text = text.replace(
        "CREATE TABLE IF NOT EXISTS analysis_resource_locks (\n    song_id INTEGER NOT NULL,\n    region TEXT NOT NULL,",
        "CREATE TABLE IF NOT EXISTS analysis_resource_locks (\n    song_id INTEGER NOT NULL,\n    phase TEXT NOT NULL,",
    )
    text = text.replace(
        "PRIMARY KEY(song_id, region)",
        "PRIMARY KEY(song_id, phase)",
    )
    text = text.replace("trg_analysis_jobs_region_lock", "trg_analysis_jobs_phase_lock")
    text = text.replace("l.region =", "l.phase =")
    text = text.replace("analysis_region_locked", "analysis_phase_locked")
    text = text.replace("regionKindSql", "phaseKindSql")
    text = text.replace("acquireAnalysisRegionLocks", "acquireAnalysisPhaseLocks")
    text = text.replace("releaseAnalysisRegionLocks", "releaseAnalysisPhaseLocks")
    text = text.replace("requestRegionCancellation", "requestPhaseCancellation")
    text = text.replace("activeRegionJobs", "activePhaseJobs")
    text = text.replace("$regions", "$phases")
    text = text.replace("$regionMarks", "$phaseMarks")
    text = text.replace("$regionExpr", "$phaseExpr")
    text = text.replace("$region", "$phase")
    text = text.replace("analysis_region_lock_scope_empty", "analysis_phase_lock_scope_empty")
    text = text.replace("analysis_region_busy_or_locked", "analysis_phase_busy_or_locked")
    text = text.replace("region_delete_", "phase_delete_")
    write(rel, text)


def patch_catalog_phase_vocabulary() -> None:
    for rel in [
        "src/Controller/CatalogController.php",
        "src/Service/CatalogService.php",
    ]:
        text = read(rel)
        text = text.replace("Region", "Phase")
        text = text.replace("region", "phase")
        text = text.replace("Regions", "Phases")
        text = text.replace("regions", "phases")
        write(rel, text)


def patch_home_template() -> None:
    rel = "templates/workbench/home.html.twig"
    text = read(rel)
    pairs = [
        (
            "Chromosome analytique : PROFILE → STEMS → CHORDS/N → LYRICS.",
            "Chaîne d’analyse : PROFILE → STEMS → CHORDS/N → LYRICS.",
        ),
        ("catalog-region-action", "catalog-phase-action"),
        ("catalog_region_delete", "catalog_phase_delete"),
        ("region:action.key", "phase:action.key"),
        ("L'ADN et l'historique seront conservés.", "Les Presets et l’historique seront conservés."),
        ("sans détruire l’ADN", "sans détruire les Presets"),
        ("chromosome_present", "analysis_chain_present"),
        ("chromosome_adn_zip", "preset_export_zip"),
        ("Exporter le chromosome ADN disponible", "Exporter les Presets disponibles"),
        ("Aucune région ADN disponible", "Aucun Preset disponible"),
        ("son chromosome complet", "sa chaîne d’analyse complète"),
    ]
    for old, new in pairs:
        text = text.replace(old, new)
    write(rel, text)


def patch_visible_templates() -> None:
    replacements = {
        "templates/lab/chords_experiment.html.twig": [
            ("l'ADN du run", "le Preset du run"),
            ("artefacts ADN", "artefacts du run"),
            ("Runs CHORDS ADN", "Runs CHORDS"),
            (">ADN<", ">Preset<"),
            ("Aucun run CHORDS ADN.", "Aucun run CHORDS."),
        ],
        "templates/lab/stems.html.twig": [
            ("ADN des artefacts", "Preset et artefacts"),
            ("Run ADN", "Run"),
            (">ADN<", ">Preset<"),
        ],
        "templates/lab/stems_job.html.twig": [
            ('href="#adn"', 'href="#preset"'),
            ('id="adn"', 'id="preset"'),
            ("ADN du run", "Preset du run"),
            ("Artefacts ADN", "Artefacts du run"),
        ],
        "templates/workbench/stems.html.twig": [
            ("l'ADN scientifique", "le registre scientifique"),
            ("piste(s) audio ADN", "piste(s) audio"),
            (">ADN<", ">Preset<"),
            ("artefacts ADN", "artefacts"),
            ("leur ADN", "leur historique"),
        ],
        "src/Service/ProfileFrenchSummary.php": [
            ("Résumé déterministe dérivé de l’ADN.", "Résumé déterministe dérivé du run PROFILE."),
        ],
    }
    for rel, pairs in replacements.items():
        p = ROOT / rel
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8")
        for old, new in pairs:
            text = text.replace(old, new)
        p.write_text(text, encoding="utf-8", newline="\n")


def patch_export() -> None:
    old = ROOT / "scripts/export-chromosome-adn.py"
    if not old.is_file():
        return
    text = old.read_text(encoding="utf-8")

    pairs = [
        ("genome_payload", "preset_payload"),
        ("genome_gene_revisions", "preset_module_revisions"),
        ("genome_region_revisions", "preset_phase_revisions"),
        ("genome_region_revision_genes", "preset_phase_revision_modules"),
        ("genome_region_revision_parents", "preset_phase_revision_parents"),
        ("scientific_run_genome", "scientific_run_preset"),
        ("genome_region_baselines", "preset_phase_baselines"),
        ("region_revision_id", "phase_revision_id"),
        ("gene_revision_id", "module_revision_id"),
        ("gene_key", "module_key"),
        ("region_revisions", "phase_revisions"),
        ("region_parents", "phase_parents"),
        ("region_genes", "phase_modules"),
        ("gene_revisions", "module_revisions"),
        ("regions", "phases"),
        ("region", "phase"),
        ("genome", "preset"),
        ("chromosome", "analysis_chain"),
        ("ADN", "PRESET"),
        ("genomic_evolution", "preset_evolution"),
        ("ezstudio.preset.export.v1", "ezstudio.preset.export.v1"),
        ("ezstudio.analysis_chain.preset.v2", "ezstudio.analysis-chain.preset-bundle.v1"),
    ]
    # Explicit schema replacements before generic words.
    text = text.replace("ezstudio.genome.export.v1", "ezstudio.preset.export.v1")
    text = text.replace("ezstudio.chromosome.adn.v2", "ezstudio.analysis-chain.preset-bundle.v1")
    for old_name, new_name in pairs:
        text = text.replace(old_name, new_name)
    text = text.replace("genome/", "presets/")
    text = text.replace("region/gene revisions", "phase/module revisions")
    text = text.replace("EZStudio_lab analysis_chain PRESET bundle v2", "EZStudio_lab Preset bundle v1")
    text = text.replace("EZSTUDIO_CHROMOSOME_ADN_EXPORT_V2_OK", "EZSTUDIO_PRESET_EXPORT_V1_OK")

    new = ROOT / "scripts/export-presets.py"
    new.write_text(text, encoding="utf-8", newline="\n")
    old.unlink()


def patch_export_controller() -> None:
    old = ROOT / "src/Controller/ChromosomeAdnController.php"
    if not old.is_file():
        return
    text = old.read_text(encoding="utf-8")
    text = text.replace("ChromosomeAdnController", "PresetExportController")
    text = text.replace(
        "/catalogue/{id<\\d+>}/chromosome-adn.zip",
        "/catalogue/{id<\\d+>}/presets.zip",
    )
    text = text.replace("chromosome_adn_zip", "preset_export_zip")
    text = text.replace("export-chromosome-adn.py", "export-presets.py")
    text = text.replace("chromosome-adn", "presets")
    text = text.replace("chromosome_adn_", "preset_export_")
    new = ROOT / "src/Controller/PresetExportController.php"
    new.write_text(text, encoding="utf-8", newline="\n")
    old.unlink()


def main() -> int:
    removed = remove_accidental_grep_artifact()
    canonicalize_analysis_registry()
    canonicalize_preset_registry()
    patch_profile_execution()
    patch_profile_validation()
    patch_database_phase_lock_vocabulary()
    patch_catalog_phase_vocabulary()
    patch_home_template()
    patch_visible_templates()
    patch_export()
    patch_export_controller()

    print("TERMINOLOGY_PRESET_R2A_CODE_APPLIED")
    print(f"accidental_grep_artifacts_removed={removed}")
    print("Persistence/UI terminology aligned; scientific algorithms unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
