from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ModuleConfigError(ValueError):
    pass


@dataclass(frozen=True)
class ModuleConfigDocument:
    path: Path
    data: dict[str, Any]
    sha256: str

    @property
    def module_id(self) -> str:
        return str(self.data["gene"]["id"])

    @property
    def gene_id(self) -> str:
        return self.module_id

    @property
    def revision(self) -> str:
        return str(self.data["gene"]["revision"])

    @property
    def phase(self) -> str:
        return str(self.data["gene"]["region"])

    @property
    def region(self) -> str:
        return self.phase

    @property
    def engine_adapter(self) -> str:
        return str(self.data["engine"]["adapter"])

    def provenance(self) -> dict[str, Any]:
        return {
            "schema": self.data["schema"],
            "gene_id": self.gene_id,
            "gene_revision": self.revision,
            "region": self.region,
            "engine_adapter": self.engine_adapter,
            "spec_path": self.path.as_posix(),
            "spec_sha256": self.sha256,
        }


def _require_mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ModuleConfigError(f"{name}_must_be_object")
    return value


def _require_string(mapping: dict[str, Any], key: str, prefix: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ModuleConfigError(f"{prefix}.{key}_must_be_non_empty_string")
    return value.strip()


def validate_module_config(data: dict[str, Any]) -> None:
    schema = data.get("schema")
    if schema != "ezstudio.gene-spec.v1":
        raise ModuleConfigError("unsupported_gene_spec_schema")

    gene = _require_mapping(data.get("gene"), "gene")
    _require_string(gene, "id", "gene")
    _require_string(gene, "revision", "gene")
    region = _require_string(gene, "region", "gene")
    if region not in {"profile", "stems", "chords", "lyrics"}:
        raise ModuleConfigError("gene.region_invalid")

    engine = _require_mapping(data.get("engine"), "engine")
    _require_string(engine, "adapter", "engine")

    if "parameters" in data and not isinstance(data["parameters"], dict):
        raise ModuleConfigError("parameters_must_be_object")
    if "decision" in data and not isinstance(data["decision"], dict):
        raise ModuleConfigError("decision_must_be_object")
    if "output" in data and not isinstance(data["output"], dict):
        raise ModuleConfigError("output_must_be_object")

    taxonomy = data.get("taxonomy")
    if taxonomy is not None:
        taxonomy = _require_mapping(taxonomy, "taxonomy")
        families = taxonomy.get("families")
        if families is not None:
            families = _require_mapping(families, "taxonomy.families")
            for family, labels in families.items():
                if not isinstance(family, str) or not family.strip():
                    raise ModuleConfigError("taxonomy_family_invalid")
                if not isinstance(labels, list) or not labels:
                    raise ModuleConfigError(f"taxonomy.{family}_must_be_non_empty_list")
                if any(not isinstance(x, str) or not x.strip() for x in labels):
                    raise ModuleConfigError(f"taxonomy.{family}_contains_invalid_label")


def load_module_config(path: str | Path) -> ModuleConfigDocument:
    p = Path(path)
    if not p.is_file():
        raise ModuleConfigError(f"gene_spec_missing:{p}")
    raw = p.read_bytes()
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ModuleConfigError(f"gene_spec_invalid_json:{exc}") from exc
    if not isinstance(data, dict):
        raise ModuleConfigError("gene_spec_root_must_be_object")
    validate_module_config(data)
    return ModuleConfigDocument(
        path=p,
        data=data,
        sha256=hashlib.sha256(raw).hexdigest(),
    )


# Legacy API aliases; persisted schema remains ezstudio.gene-spec.v1 in R1.
GeneSpecError = ModuleConfigError
GeneSpecDocument = ModuleConfigDocument
validate_gene_spec = validate_module_config
load_gene_spec = load_module_config
