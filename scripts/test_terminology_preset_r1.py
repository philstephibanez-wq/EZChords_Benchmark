from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "python/ezstudio/pipeline/profile"
RUNTIME = ROOT / "python/ezstudio/runtime"

required = [
    ROOT/"src/Service/AnalysisRunRegistry.php",
    ROOT/"src/Service/PresetRegistry.php",
    PROFILE/"gene.py",
    PROFILE/"gene_registry.py",
    PROFILE/"runner.py",
    RUNTIME/"gene_spec.py",
]
for p in required:
    assert p.is_file(), p

for p in [
    PROFILE/"gene.py",
    PROFILE/"gene_registry.py",
    PROFILE/"runner.py",
    RUNTIME/"gene_spec.py",
    RUNTIME/"engine_registry.py",
]:
    ast.parse(p.read_text(encoding="utf-8"), filename=str(p))

module_text = (PROFILE/"gene.py").read_text(encoding="utf-8")
assert "class ModuleConfig:" in module_text
assert "module_id: str" in module_text
assert "class ModuleContext:" in module_text
assert "def run_module(" in module_text
assert "GeneSpec = ModuleConfig" in module_text
assert "GeneContext = ModuleContext" in module_text
assert "run_gene = run_module" in module_text

registry_text = (PROFILE/"gene_registry.py").read_text(encoding="utf-8")
assert "class ModuleRegistry:" in registry_text
assert ".module_id" in registry_text
assert "GeneRegistry = ModuleRegistry" in registry_text

runner_text = (PROFILE/"runner.py").read_text(encoding="utf-8")
assert "def build_module_registry(" in runner_text
assert "ModuleRegistry()" in runner_text
assert "ModuleConfig(" in runner_text
assert "ModuleContext(" in runner_text
assert "build_gene_registry = build_module_registry" in runner_text
assert '"gene_registry"' in runner_text
assert '"genome"' in runner_text

cfg_text = (RUNTIME/"gene_spec.py").read_text(encoding="utf-8")
assert "class ModuleConfigDocument:" in cfg_text
assert "class ModuleConfigError(" in cfg_text
assert "def module_id(" in cfg_text
assert "def phase(" in cfg_text
assert "def validate_module_config(" in cfg_text
assert "def load_module_config(" in cfg_text
assert "GeneSpecDocument = ModuleConfigDocument" in cfg_text
assert 'ezstudio.gene-spec.v1' in cfg_text

dna = (ROOT/"src/Service/DnaRegistry.php").read_text(encoding="utf-8")
genome = (ROOT/"src/Service/GenomeRegistry.php").read_text(encoding="utf-8")
assert "scientific_runs" in dna
assert "genome_gene_revisions" in genome
assert "genome_region_revisions" in genome

print("TERMINOLOGY_PRESET_R1_CONTRACT_OK")
print("Canonical names active; legacy persisted contracts preserved")
