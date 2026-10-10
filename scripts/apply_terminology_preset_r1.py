from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(rel: str) -> str:
    p = ROOT / rel
    if not p.is_file():
        raise RuntimeError(f"required_file_missing:{rel}")
    return p.read_text(encoding="utf-8")

def write(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8", newline="\n")

# PHP canonical facades; persistence/schema unchanged.
for rel, decl in [
    ("src/Service/DnaRegistry.php", "final class DnaRegistry"),
    ("src/Service/GenomeRegistry.php", "final class GenomeRegistry"),
]:
    text = read(rel)
    if decl not in text:
        raise RuntimeError(f"expected_marker_missing:{rel}:{decl}")
    write(rel, text.replace(decl, decl.replace("final class", "class"), 1))

write("src/Service/AnalysisRunRegistry.php", """<?php

namespace App\\Service;

/**
 * Canonical terminology facade for scientific runs and artifacts.
 * Legacy DnaRegistry remains the persistence implementation during R1.
 */
final class AnalysisRunRegistry extends DnaRegistry
{
}
""")

write("src/Service/PresetRegistry.php", """<?php

namespace App\\Service;

/**
 * Canonical terminology facade for module/phase preset revisions.
 * Legacy GenomeRegistry remains the persistence implementation during R1.
 */
final class PresetRegistry extends GenomeRegistry
{
}
""")

for p in (ROOT / "src").rglob("*.php"):
    rel = p.relative_to(ROOT).as_posix()
    if rel in {
        "src/Service/DnaRegistry.php",
        "src/Service/GenomeRegistry.php",
        "src/Service/AnalysisRunRegistry.php",
        "src/Service/PresetRegistry.php",
    }:
        continue
    text = p.read_text(encoding="utf-8")
    text = text.replace("use App\\Service\\DnaRegistry;", "use App\\Service\\AnalysisRunRegistry;")
    text = text.replace("use App\\Service\\GenomeRegistry;", "use App\\Service\\PresetRegistry;")
    text = re.sub(r"\bDnaRegistry\b", "AnalysisRunRegistry", text)
    text = re.sub(r"\bGenomeRegistry\b", "PresetRegistry", text)
    text = text.replace("AnalysisRunRegistry $dna", "AnalysisRunRegistry $runRegistry")
    text = text.replace("PresetRegistry $genome", "PresetRegistry $presets")
    text = text.replace("$this->dna", "$this->runRegistry")
    text = text.replace("$this->genome", "$this->presets")
    text = text.replace("$dna->", "$runRegistry->")
    text = text.replace("$genome->", "$presets->")
    p.write_text(text, encoding="utf-8", newline="\n")

export_controller = ROOT / "src/Controller/ChromosomeAdnController.php"
if export_controller.is_file():
    text = export_controller.read_text(encoding="utf-8")
    text = text.replace("EZStudio_CHROMOSOME_ADN_", "EZStudio_PRESET_")
    export_controller.write_text(text, encoding="utf-8", newline="\n")

dna_templates = ROOT / "templates/dna"
if dna_templates.is_dir():
    for p in dna_templates.rglob("*.twig"):
        text = p.read_text(encoding="utf-8")
        for old, new in [
            ("ADN", "Preset"),
            ("Chromosome", "Chaîne"),
            ("chromosome", "chaîne"),
            ("Régions", "Phases"),
            ("régions", "phases"),
            ("Région", "Phase"),
            ("région", "phase"),
            ("Gènes", "Modules"),
            ("gènes", "modules"),
            ("Gène", "Module"),
            ("gène", "module"),
        ]:
            text = text.replace(old, new)
        p.write_text(text, encoding="utf-8", newline="\n")

# Python PROFILE: canonical Module terminology; persisted keys unchanged.
gene_py = "python/ezstudio/pipeline/profile/gene.py"
text = read(gene_py)
for marker in ("class GeneSpec:", "class GeneContext:", "def run_gene("):
    if marker not in text:
        raise RuntimeError(f"expected_marker_missing:{gene_py}:{marker}")
text = text.replace("class GeneSpec:", "class ModuleConfig:")
text = text.replace("class GeneContext:", "class ModuleContext:")
text = text.replace("def run_gene(", "def run_module(")
text = text.replace("    gene_id: str\n", "    module_id: str\n")
text = text.replace("spec: GeneSpec", "config: ModuleConfig")
text = text.replace("context: GeneContext", "context: ModuleContext")
text = text.replace("spec.", "config.")
text = text.replace('"id": config.gene_id,', '"id": config.module_id,')
text = text.replace("gene_id=config.gene_id", "gene_id=config.module_id")
text += "\n\n# Legacy aliases retained for terminology-migration compatibility.\nGeneSpec = ModuleConfig\nGeneContext = ModuleContext\nrun_gene = run_module\n"
write(gene_py, text)

registry_py = "python/ezstudio/pipeline/profile/gene_registry.py"
text = read(registry_py)
if "class GeneRegistry:" not in text:
    raise RuntimeError(f"expected_marker_missing:{registry_py}:class GeneRegistry")
text = text.replace("GeneContext", "ModuleContext")
text = text.replace("GeneSpec", "ModuleConfig")
text = text.replace("run_gene", "run_module")
text = text.replace("class GeneRegistry:", "class ModuleRegistry:")
text = text.replace(') -> "GeneRegistry":', ') -> "ModuleRegistry":')
text = text.replace(".gene_id", ".module_id")
text += "\n\n# Legacy alias retained for terminology-migration compatibility.\nGeneRegistry = ModuleRegistry\n"
write(registry_py, text)

runner_py = "python/ezstudio/pipeline/profile/runner.py"
text = read(runner_py)
text = text.replace("from gene import GeneContext, GeneSpec",
                    "from gene import ModuleContext, ModuleConfig")
text = text.replace("from gene_registry import GeneRegistry",
                    "from gene_registry import ModuleRegistry")
text = text.replace("def build_gene_registry(", "def build_module_registry(")
text = text.replace(") -> GeneRegistry:", ") -> ModuleRegistry:")
text = text.replace("GeneRegistry()", "ModuleRegistry()")
text = text.replace("GeneSpec(", "ModuleConfig(")
text = text.replace("GeneContext(", "ModuleContext(")
text = text.replace("gene_id=", "module_id=")
text = text.replace("gene_registry_result", "module_registry_result")
text = text.replace("build_gene_registry(", "build_module_registry(")
text = text.replace("registry = build_module_registry(", "module_registry = build_module_registry(")
text = text.replace("registry.run(", "module_registry.run(")
text = text.replace("registry.genome_manifest(", "module_registry.genome_manifest(")
if "build_gene_registry = build_module_registry" not in text:
    pos = text.find("\ndef main()")
    if pos < 0:
        raise RuntimeError("runner_main_marker_missing")
    text = text[:pos] + "\n\n# Legacy callable alias during terminology migration.\nbuild_gene_registry = build_module_registry\n" + text[pos:]
write(runner_py, text)

modules_dir = ROOT / "python/ezstudio/pipeline/profile/genes"
if modules_dir.is_dir():
    for p in modules_dir.glob("*.py"):
        text = p.read_text(encoding="utf-8")
        text = text.replace("from gene import GeneContext", "from gene import ModuleContext")
        text = text.replace("GeneContext", "ModuleContext")
        p.write_text(text, encoding="utf-8", newline="\n")

# Runtime config API: canonical names, legacy on-disk schema compatibility.
spec_py = "python/ezstudio/runtime/gene_spec.py"
text = read(spec_py)
for old, new in [
    ("GeneSpecError", "ModuleConfigError"),
    ("GeneSpecDocument", "ModuleConfigDocument"),
    ("def validate_gene_spec(", "def validate_module_config("),
    ("def load_gene_spec(", "def load_module_config("),
    ("validate_gene_spec(data)", "validate_module_config(data)"),
]:
    text = text.replace(old, new)

old = '    @property\n    def gene_id(self) -> str:\n        return str(self.data["gene"]["id"])\n'
new = '    @property\n    def module_id(self) -> str:\n        return str(self.data["gene"]["id"])\n\n    @property\n    def gene_id(self) -> str:\n        return self.module_id\n'
if old not in text:
    raise RuntimeError("gene_spec_gene_id_property_missing")
text = text.replace(old, new)

old = '    @property\n    def region(self) -> str:\n        return str(self.data["gene"]["region"])\n'
new = '    @property\n    def phase(self) -> str:\n        return str(self.data["gene"]["region"])\n\n    @property\n    def region(self) -> str:\n        return self.phase\n'
if old not in text:
    raise RuntimeError("gene_spec_region_property_missing")
text = text.replace(old, new)

text += "\n\n# Legacy API aliases; persisted schema remains ezstudio.gene-spec.v1 in R1.\nGeneSpecError = ModuleConfigError\nGeneSpecDocument = ModuleConfigDocument\nvalidate_gene_spec = validate_module_config\nload_gene_spec = load_module_config\n"
write(spec_py, text)

runtime_dir = ROOT / "python/ezstudio/runtime"
if runtime_dir.is_dir():
    for p in runtime_dir.rglob("*.py"):
        if p.name == "gene_spec.py":
            continue
        text = p.read_text(encoding="utf-8")
        text = text.replace("GeneSpecDocument", "ModuleConfigDocument")
        text = text.replace("load_gene_spec", "load_module_config")
        text = text.replace("Gene Spec", "Module Config")
        text = text.replace("gene spec", "module config")
        p.write_text(text, encoding="utf-8", newline="\n")

clap_wrapper = ROOT / "python/ezstudio/pipeline/profile/genes/semantic_clap_open_vocab.py"
if clap_wrapper.is_file():
    text = clap_wrapper.read_text(encoding="utf-8")
    text = text.replace("load_gene_spec", "load_module_config")
    text = re.sub(r"\bspec\b", "module_config", text)
    clap_wrapper.write_text(text, encoding="utf-8", newline="\n")

engine_registry = ROOT / "python/ezstudio/runtime/engine_registry.py"
if engine_registry.is_file():
    text = engine_registry.read_text(encoding="utf-8")
    text = text.replace("A Gene Spec points", "A Module Config points")
    text = text.replace("Gene Spec.", "Module Config.")
    engine_registry.write_text(text, encoding="utf-8", newline="\n")

print("TERMINOLOGY_PRESET_R1_APPLIED")
print("Canonical vocabulary introduced in code")
print("Scientific algorithms/settings unchanged")
print("SQLite and persisted scientific JSON contracts unchanged")
print("Legacy aliases retained for regression safety")
